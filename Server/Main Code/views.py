#-*- coding: euc-kr -*-

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json, os, random, shutil
import pandas as pd
import dataframe_image as dfi
from matplotlib import font_manager, rc
import datetime
from . import models # DB ��
from . import fp_ip # OCR ó��
from . import fp_ip2 # ���ڵ� ó��
from . import response_select # OCR ���� ���� �޴� ó��

# �ѱ� ��Ʈ ����
font_fname = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
font_name = font_manager.FontProperties(fname=font_fname).get_name()
rc('font', family=font_name)

# Item Type Dictionary
IT = dict()
IT['�����']=['��','Ŀ��','��������','ź������','�̿�����','��ȿ����','���� �Է�']
IT['�ַ�']=['����','����','Ź��','������','����Ű','�귣��','���� �Է�']
IT['������ǰ']=['����','���������','����','ġ��','����','���Ʈ','���� �Է�']
IT['���']=['�Ҹ�','���','Į����','�и�','�ø�','�̸�','���� �Է�']
IT['�κ�,����']=['�κ�','���κ�','�����κ�','��','����','���','���� �Է�']
IT['����']=['�Ұ��','�������','�߰��','��','�ҽ���','������','���� �Է�']
IT['���깰��']=['����','����','��','����','����','��/����','���� �Է�']
IT['�Ｎ��ǰ��']=['���ö�','�ܹ���','���','������ġ','����','����','���� �Է�']
IT['����,��,����']=['����','��','����','���ݸ�','��','��','���� �Է�']
IT['������']=['���̽�ũ��','�ϵ�','������','����','����ũ','����','���� �Է�']
IT['��Ÿ']=[]

# DB �Ϻ� �ʱ�ȭ (id, cicode ����)
def init_db(user):
    user.menu = user.status = user.cinum = 0
    user.citype = user.ciname = user.b_choice = user.d_choice = user.cidesc = 'none'
    user.cidate = None
    user.save()

# �ùٸ��� ���� �Է� -> �ٽ� �õ�
def regame():
    return JsonResponse({
        'version': "2.0",
        'template': {
            'outputs': [{
                'simpleText': {
                    'text': '�ùٸ��� ���� �Է��Դϴ�. �ٽ� �õ����ּ���.'
                }
            }],
            'quickReplies': [
                {
                'label': '�ٽ� �õ�',
                'action': 'message',
                'messageText': '�ٽ� �õ�'
                },
                {
                'label': 'ó������',
                'action': 'message',
                'messageText': 'ó������'
                }
            ]
        }
    })

# ���� �߻� -> ó������
def init_rs():
    return JsonResponse({
        'version': "2.0",
        'template': {
            'outputs': [{
                'simpleText': {
                    'text': '�ùٸ��� ���� �Է��Դϴ�. ó������ �ٽ� �������ּ���.'
                }
            }],
            'quickReplies': [
                {
                'label': 'ó������',
                'action': 'message',
                'messageText': 'ó������'
                }
            ]
        }
    })

# DataFrame Hightlight function
def draw_color_cell(x,color):
    color = f'background-color:{color}'
    return color

# date1 < date2 -> True, else -> False
def last_day(date1,date2):
    year1 = int(date1[0:4]); year2 = int(date2[0:4]);
    month1 = int(date1[5:7]); month2 = int(date2[5:7]);
    day1 = int(date1[8:10]); day2 = int(date2[8:10]);
    if year1 < year2:
        return True
    elif year1 == year2 and month1 < month2:
        return True
    elif year1 == year2 and month1 == month2 and day1 < day2:
        return True
    else:
        return False

# DB -> DataFrame -> Image URL (ip/userId/random_table.jpg)
def DB2ImageUrl(table,userId,menu):
    # table row num
    row_num = table.count()

    # DB -> DataFrame
    df = pd.DataFrame.from_records(table.values())

    # '�������' ��¥ ����Ʈ
    day_default_list = df[['idate']].values.tolist()
    day_list = [str(day_default_list[i][0].strftime("%Y-%m-%d")) for i in range(0, row_num)]

    # ���� ��¥ Ȯ��
    dt_now = datetime.datetime.now()
    today = str(dt_now.date())

    # �� �̸� ���� (0~row_num-1 -> 1:num)
    df.index = [str(i) for i in range(1, row_num + 1)]

    # �̻�ġ ó�� (������� �����ؼ� �̻�ġ�� ����� ���)
    for i, uday in enumerate(day_list):
        # �̻�ġ Ȯ��
        if uday == "2099-12-31":
            # ���ĵ� �����̹Ƿ� i�� ���ϴ� ��� �̻�ġ
            # df���� ��������� ''�� ����
            for j in range(i,len(day_list)):
                df.loc[str(j+1),'idate']=''
            break

    # �޴� = ����Ʈ Ȯ��
    if menu == 2:
        # ������ ������ ���� �� ������ ������ �� �̸� ����
        df = df[['itype', 'iname', 'idesc', 'inum', 'idate']]
        df.rename(columns={"itype": "�з�", "iname": "ǰ��", "idesc": "��", "inum": "����", "idate": "�������"}, inplace=True)

        # ��������� ���� �������� ����� ó��
        for i, uday in enumerate(day_list):
            # ��������� �� ���� �������� �߰�
            if last_day(uday,today) == False:
                # ù ��(i=0)���� �߰� -> ��� �������� ������� �� ����
                # ù ���� �ƴ� ������ �߰� -> ��������� ���� �������� �� �� �̻� ����
                if i != 0:
                    idx = pd.IndexSlice
                    slice=idx[idx[:str(i)],idx[:]]
                    df = df.style.applymap(draw_color_cell, color='#ffff66', subset=slice)
                break
            # ���� ��������� ���� ��������
            elif i == row_num - 1:
                idx = pd.IndexSlice
                slice = idx[idx[:str(i+1)], idx[:]]
                df = df.style.applymap(draw_color_cell, color='#ffff66', subset=slice)

    # �޴� = ������ ���� (����� ������ Ȯ��, �ڵ� Ȯ��, ����� ����Ʈ Ȯ��)
    else:
        # ������ ������ ���� �� ������ ������ �� �̸� ����
        df = df[['icode','itype', 'iname', 'idesc', 'inum', 'idate']]
        df.rename(columns={"icode":"�ڵ�","itype": "�з�", "iname": "ǰ��", "idesc": "��", "inum": "����", "idate": "�������"}, inplace=True)

        # ��������� ���� �������� ����� ó��
        for i, uday in enumerate(day_list):
            # ��������� �� ���� �������� �߰�
            if last_day(uday,today) == False:
                # ù ��(i=0)���� �߰� -> ��� �������� ������� �� ����
                if i==0:
                    df = df.style.applymap(draw_color_cell, color='#ff6666', subset=pd.IndexSlice[:, '�ڵ�'])
                # ù ���� �ƴ� ������ �߰� -> ��������� ���� �������� �� �� �̻� ����
                else:
                    idx = pd.IndexSlice
                    slice=idx[idx[:str(i)],idx[:]]
                    df=df.style\
                        .applymap(draw_color_cell, color='#ffff66', subset=slice)\
                        .applymap(draw_color_cell, color='#ff6666', subset=pd.IndexSlice[:, '�ڵ�'])
                break
            # ���� ��������� ���� ��������
            elif i == row_num-1:
                idx = pd.IndexSlice
                slice = idx[idx[:str(i+1)], idx[:]]
                df=df.style\
                    .applymap(draw_color_cell, color='#ffff66', subset=slice) \
                    .applymap(draw_color_cell, color='#ff6666', subset=pd.IndexSlice[:, '�ڵ�'])

    # �̹��� ���� ��� ����
    _dir = os.path.join(settings.STATIC_ROOT, userId)  # ���丮 ��� ����
    _random = str(random.randint(1, 100))  # ���� ���� ����
    _target = os.path.join(_dir, _random + '_table.jpg')  # ���� ��� �� �̸� ���� (�������� �����ؼ� ���� ������Ʈ ���� �� ���⵵��)
    _url = 'http://125.180.136.226/static/' + userId + '/' + _random + '_table.jpg'

    # ���� �����Ͱ� ���Ե� ���丮 ����� ���� <���� ����>
    if os.path.exists(_dir):
        shutil.rmtree(_dir)
    os.mkdir(_dir)  # �����Ѵ�� ���丮 ����

    # �̹��� ����
    # df -> image (encoding �ʿ���,/home/ubuntu/jps/jps_ve/lib/python3.8/site-packages/dataframe_image/_screenshot.py)
    dfi.export(df, _target, max_cols=-1, max_rows=-1)  # ���� ���� (df -> image)

    return _url

# Create your views here.
def home_list(request):
    dt_now = datetime.datetime.now()
    day=dt_now.date()
    return JsonResponse({
      'server':day
    })

@csrf_exempt
def message(request):
    answer = ((request.body).decode('utf-8'))
    return_json_str = json.loads(answer)
    return_str = return_json_str['userRequest']['utterance'] # ����� ��ȭ
    return_id = return_json_str['userRequest']['user']['id'] # ����� ID
    userId=str(return_id)[0:10]
    print(return_str)

    # ȸ�� ã��
    try:
        user=models.User.objects.get(id=userId)
    except:
        user=0

    # ��ϵ� ȸ���� ���
    if user:
        # =================================================
        # << �޴� ���� â >>
        # ��ȭ = '������' or 'ó������'
        # [�޴� ����(menu status) ��� ���� ����]
        # =================================================

        if (return_str == "��������") or (return_str == "������") or (return_str == "��") or (return_str == "ó������") or (
                return_str == "ó��"):

            # DB �ʱ�ȭ
            init_db(user)

            # response
            return JsonResponse({
                'version': "2.0",
                'template': {
                    'outputs': [{
                        'simpleText': {
                            'text': "����� ������� ���� ê�� '������'�Դϴ�.\n\n������ ���͵帱���?"
                        }
                    }],
                    'quickReplies': [
                        {
                            'label': '������ ����',
                            'action': 'message',
                            'messageText': '������ ����'
                        },
                        {
                            'label': '����Ʈ Ȯ��',
                            'action': 'message',
                            'messageText': '����Ʈ Ȯ��'
                        },
                        {
                            'label': '������ ����',
                            'action': 'message',
                            'messageText': '������ ����'
                        },
                        {
                            'label': 'ȸ�� Ż��',
                            'action': 'message',
                            'messageText': 'ȸ�� Ż��'
                        }
                    ]
                }
            })

        # =================================================
        # �޴� ���� ����
        # =================================================

        if user.menu == 0:
            # ��ȭ = '������ ����/�߰�' or <Ư�� ���̽�:�з� ���� -> ǰ�� �Է� �� "��������">
            if (return_str == "������ ����") or (return_str == "������ �߰�"):
                # DB ����
                user.menu = 1 # --> �޴�1
                user.save()

            # ��ȭ = '����Ʈ Ȯ��'
            elif return_str == "����Ʈ Ȯ��":
                # DB ����
                user.menu = 2 # --> �޴�2
                user.save()

            # ��ȭ = '������ ����'
            elif return_str == "������ ����":
                # DB ����
                user.menu = 3  # --> �޴�3
                user.save()

            # ��ȭ = 'ȸ�� Ż��'
            elif return_str == "ȸ�� Ż��":
                # DB ����
                user.menu = 4  # --> �޴�4
                user.save()

            # �ùٸ��� ���� �޴� �Է�
            else:
                # DB �ʱ�ȭ �� response
                init_db(user)
                return init_rs()

        # =================================================
        # �޴�1 ('������ ����' ��ȭ ����)
        # =================================================
        if user.menu == 1:
            # --------------------
            # ������ ���� ��� ����
            # --------------------
            if user.status == 0 or (user.status == 0.5 and return_str == "�ٽ� �õ�") or ((user.status == 1 or user.status == 11) and return_str == "��������") or (user.status == 12 and return_str == "�ƴϿ�"):
                # <Ư�� ���̽�> ������ ���� ��� ���� �� �̻��� ������ �Է� -> �ٽ� �õ�
                # <Ư�� ���̽�> ������ ���� ��� ���� -> ��������
                # <Ư�� ���̽�> ������ ���� ��� ���� -> (���ڵ� ����) ���ڵ� ������ ���� -> �ùٸ��� ���� ���� ȹ��('�ƴϿ�')
                if (user.status == 0.5 and return_str == "�ٽ� �õ�") or ((user.status == 1 or user.status == 11) and return_str == "��������") or (user.status == 12 and return_str == "�ƴϿ�"):
                    re=1
                else:
                    re=0

                # DB ����
                user.b_choice = 'none'  # ���ڵ� �̿� ���� �ʱ�ȭ ('�ƴϿ�' ���)
                user.citype = user.ciname = user.cidesc = 'none'  # ������ ���� ���� �ʱ�ȭ ('�ƴϿ�' ���)
                user.status = 0.5  # --> �޴� ���� �Ϸ�, ������ ���� ��� ���� ����
                user.save()

                # �ٽ� �õ� Ȯ��
                if re==1:
                    txt="�ٽ� "
                else:
                    txt=""

                # response
                return JsonResponse({
                    'version': "2.0",
                    'template': {
                        'outputs': [{
                            'simpleText': {
                                'text': "������ ���� ����� "+txt+"�������ּ���!!"
                            }
                        }],
                        'quickReplies': [
                            {
                                'label': '���� ����',
                                'action': 'message',
                                'messageText': '���� ����'
                            },
                            {
                                'label': '���ڵ� ����',
                                'action': 'message',
                                'messageText': '���ڵ� ����'
                            },
                            {
                                'label': 'ó������',
                                'action': 'message',
                                'messageText': 'ó������'
                            }
                        ]
                    }
                })

            # -------------------------
            # ������ ���� ��� ���� ����
            # -------------------------
            if user.status == 0.5 or (user.status == 1 and return_str == "�ٽ� �õ�") or (user.status == 2 and return_str == "��������") or\
                    (user.status == 11 and return_str == "�ٽ� �õ�") or (user.status == 12 and return_str == "�ٽ� �õ�" and user.citype == "none") or\
                    (user.status == 12 and return_str == "��������"):

                # <Ư�� ���̽�> (���� ����) �̹��� �з� ���� �� �߸��� �Է� -> �ٽ� �з� ����
                # <Ư�� ���̽�> (���� ����) �̹��� �з� ���� -> �̹��� ǰ�� ���� �� '��������' -> �ٽ� �з� ����
                # <Ư�� ���̽�> (���ڵ� ����) ���ڵ� ������ �������� �ʰ� �̻��� �Է� -> �ٽ� ���ڵ� ���� �䱸
                # <Ư�� ���̽�> (���ڵ� ����) ���ڵ� ������ ���� �� �ùٸ��� ���� ������ ���� ȹ�� -> �̻��� ������ �Է� -> �ٽ� ���ڵ� ���� �䱸
                # <Ư�� ���̽�> (���ڵ� ����) ���ڵ� ������ ���� �� ������ ���� ȹ�� -> '��������' -> �ٽ� ���ڵ� ���� �䱸

                # (1) ���� ����
                if return_str == "���� ����" or (user.status == 1 and return_str == "�ٽ� �õ�") or (user.status == 2 and return_str == "��������"):
                    # DB ����
                    user.status = 1  # --> ������ ���� ��� ���� �Ϸ�(���� ����), �з� ���� ����
                    user.save()

                    # response
                    return JsonResponse({
                        'version': "2.0",
                        'template': {
                            'outputs': [{
                                "carousel": {
                                    "type": "basicCard",
                                    "items":
                                        [
                                            {
                                                "title": "�����",
                                                "description": "(��,Ŀ��,����/ź��/�̿�/��ȿ����)",
                                                "thumbnail": {
                                                    "imageUrl": "http://125.180.136.226/static/class1.jpg"
                                                },
                                                "buttons": [
                                                    {
                                                        "action": "message",
                                                        "label": "�����",
                                                        "messageText": "�����"
                                                    }
                                                ]
                                            },
                                            {
                                                "title": "�ַ�",
                                                "description": "(����,����,Ź��,������,����Ű,�귣��)",
                                                "thumbnail": {
                                                    "imageUrl": "http://125.180.136.226/static/class2.jpg"
                                                },
                                                "buttons": [
                                                    {
                                                        "action": "message",
                                                        "label": "�ַ�",
                                                        "messageText": "�ַ�"
                                                    }
                                                ]
                                            },
                                            {
                                                "title": "������ǰ",
                                                "description": "(����,����,ġ��,����,���Ʈ)",
                                                "thumbnail": {
                                                    "imageUrl": "http://125.180.136.226/static/class3.jpg"
                                                },
                                                "buttons": [
                                                    {
                                                        "action": "message",
                                                        "label": "������ǰ",
                                                        "messageText": "������ǰ"
                                                    }
                                                ]
                                            },
                                            {
                                                "title": "���",
                                                "description": "(�Ҹ�,���,Į����,�и�,�ø�,�̸�)",
                                                "thumbnail": {
                                                    "imageUrl": "http://125.180.136.226/static/class4.jpg"
                                                },
                                                "buttons": [
                                                    {
                                                        "action": "message",
                                                        "label": "���",
                                                        "messageText": "���"
                                                    }
                                                ]
                                            },
                                            {
                                                "title": "�κ�,����",
                                                "description": "(�κ�,���κ�,�����κ�,��,����,���)",
                                                "thumbnail": {
                                                    "imageUrl": "http://125.180.136.226/static/class5.jpg"
                                                },
                                                "buttons": [
                                                    {
                                                        "action": "message",
                                                        "label": "�κ�,����",
                                                        "messageText": "�κ�,����"
                                                    }
                                                ]
                                            },
                                            {
                                                "title": "����",
                                                "description": "(�Ұ��,�������,�߰��,��,�ҽ���,������)",
                                                "thumbnail": {
                                                    "imageUrl": "http://125.180.136.226/static/class6.jpg"
                                                },
                                                "buttons": [
                                                    {
                                                        "action": "message",
                                                        "label": "����",
                                                        "messageText": "����"
                                                    }
                                                ]
                                            },
                                            {
                                                "title": "���깰��",
                                                "description": "(����,����,��,����,����,��,����)",
                                                "thumbnail": {
                                                    "imageUrl": "http://125.180.136.226/static/class7.jpg"
                                                },
                                                "buttons": [
                                                    {
                                                        "action": "message",
                                                        "label": "���깰��",
                                                        "messageText": "���깰��"
                                                    }
                                                ]
                                            },
                                            {
                                                "title": "�Ｎ��ǰ��",
                                                "description": "(���ö�,�ܹ���,���,������ġ,����,����)",
                                                "thumbnail": {
                                                    "imageUrl": "http://125.180.136.226/static/class8.jpg"
                                                },
                                                "buttons": [
                                                    {
                                                        "action": "message",
                                                        "label": "�Ｎ��ǰ��",
                                                        "messageText": "�Ｎ��ǰ��"
                                                    }
                                                ]
                                            },
                                            {
                                                "title": "����,��,����",
                                                "description": "(����,��,����,���ݸ�,��,��)",
                                                "thumbnail": {
                                                    "imageUrl": "http://125.180.136.226/static/class9.jpg"
                                                },
                                                "buttons": [
                                                    {
                                                        "action": "message",
                                                        "label": "����,��,����",
                                                        "messageText": "����,��,����"
                                                    }
                                                ]
                                            },
                                            {
                                                "title": "������",
                                                "description": "(���̽�ũ��,�ϵ�,������,����,����ũ,����)",
                                                "thumbnail": {
                                                    "imageUrl": "http://125.180.136.226/static/class10.jpg"
                                                },
                                                "buttons": [
                                                    {
                                                        "action": "message",
                                                        "label": "������",
                                                        "messageText": "������"
                                                    }
                                                ]
                                            }, {
                                            "title": "��Ÿ",
                                            "description": "(��Ÿ ����)",
                                            "thumbnail": {
                                                "imageUrl": "http://125.180.136.226/static/class11.jpg"
                                            },
                                            "buttons": [
                                                {
                                                    "action": "message",
                                                    "label": "��Ÿ",
                                                    "messageText": "��Ÿ"
                                                }
                                            ]
                                        }
                                        ]
                                }
                            }
                            ],
                            'quickReplies': [
                                {
                                    'label': '��������',
                                    'action': 'message',
                                    'messageText': '��������'
                                },
                                {
                                    'label': 'ó������',
                                    'action': 'message',
                                    'messageText': 'ó������'
                                }
                            ]
                        }
                    })

                # (2) ���ڵ� ����
                elif return_str == "���ڵ� ����" or (user.status == 11 and return_str == "�ٽ� �õ�") or (user.status == 12 and return_str == "��������") or \
                        (user.status == 12 and return_str == "�ٽ� �õ�" and user.citype == "none"):

                    # DB ����
                    user.b_choice = 'none' # ���ڵ� �̿� ���� �ʱ�ȭ ('��������' ���)
                    user.citype = user.ciname = user.cidesc = 'none' # ������ ���� ���� �ʱ�ȭ ('��������' ���)
                    user.status = 11 # --> ������ ���� ��� ���� �Ϸ�(���ڵ� ����), ���ڵ� �̹��� ���� ����
                    user.save()

                    # response
                    return JsonResponse({
                        'version': "2.0",
                        'template': {
                            'outputs': [{
                                'simpleText': {
                                    'text': "���ڵ尡 ���Ե� �̹����� �������ּ���. ���ڵ尡 �ָ� �ְų� ȭ���� �� ���� �̹����� �νķ��� �������ϴ�."
                                }
                            }],
                            'quickReplies': [
                                {
                                    'label': '��������',
                                    'action': 'message',
                                    'messageText': '��������'
                                },
                                {
                                    'label': 'ó������',
                                    'action': 'message',
                                    'messageText': 'ó������'
                                }
                            ]
                        }
                    })

                # �̻��� ��ȭ
                else:
                    # �ٽ� ����
                    return regame()

            # --------------
            # ���ڵ� ���� ����
            # --------------
            if user.status == 11 or (user.status == 12 and return_str == "�ٽ� �õ�" and user.citype != "none") or (user.status == 5 and user.b_choice == "��" and return_str=="��������"):
                # <Ư�� ���̽�> ������ ������ Ȯ���ϴ� �������� �ùٸ��� ���� �Է�
                # <Ư�� ���̽�> (���ڵ� ����) ���ڵ� ���� ó�� �� ������ ���� ���� �� '��������' -> �ٽ� ���ڵ� ���� �䱸
                if (user.status == 12 and return_str == "�ٽ� �õ�" and user.citype != "none") or (user.status == 5 and user.b_choice == "��" and return_str=="��������"):
                    # DB ����
                    user.status = 12  # --> ������ ���� ȹ�� �� Ȯ�� ����
                    user.save()

                    # response
                    return JsonResponse({
                        'version': "2.0",
                        'template': {
                            'outputs': [{
                                'simpleText': {
                                    'text': "�ùٸ� ������ �������� Ȯ�����ּ���!!\n\n�� �з�: " + user.citype + "\n�� ǰ��: " + user.ciname + "\n�� �� ����: " + user.cidesc + "\n\n��(��) �½��ϱ�?"
                                }
                            }],
                            'quickReplies': [
                                {
                                    'label': '��',
                                    'action': 'message',
                                    'messageText': '��'
                                },
                                {
                                    'label': '�ƴϿ�',
                                    'action': 'message',
                                    'messageText': '�ƴϿ�'
                                },
                                {
                                    'label': '��������',
                                    'action': 'message',
                                    'messageText': '��������'
                                },
                                {
                                    'label': 'ó������',
                                    'action': 'message',
                                    'messageText': 'ó������'
                                }
                            ]
                        }
                    })

                # <�Ϲ� ���̽�>
                else:
                    # �̹����� �Է����� �Դ��� Ȯ��
                    try:
                        return_img = return_json_str['userRequest']['params']['media']['url']
                        print(return_img)

                        # DB ����
                        user.status = 12  # --> ���ڵ� ���� �Ϸ�, ������ ���� ȹ�� �� Ȯ�� ����
                        user.save()

                        # ������ ���� ��
                        if return_img:
                            # ���ڵ�� ������ ���� ȹ���ϱ�
                            infor_list=fp_ip2.barcode_infor(return_img)

                            # ������ ���� ȹ�� �Ϸ�
                            if infor_list:
                                # DB ����
                                user.citype=infor_list[0] # �з�
                                user.ciname=infor_list[1] # ǰ��
                                user.cidesc=infor_list[2] # �� ����
                                user.save()

                                # response
                                return JsonResponse({
                                    'version': "2.0",
                                    'template': {
                                        'outputs': [{
                                            'simpleText': {
                                                'text': "�ùٸ� ������ �������� Ȯ�����ּ���!!\n\n�� �з�: " + user.citype + "\n�� ǰ��: " + user.ciname + "\n�� �� ����: " + user.cidesc + "\n\n��(��) �½��ϱ�?"
                                            }
                                        }],
                                        'quickReplies': [
                                            {
                                                'label': '��',
                                                'action': 'message',
                                                'messageText': '��'
                                            },
                                            {
                                                'label': '�ƴϿ�',
                                                'action': 'message',
                                                'messageText': '�ƴϿ�'
                                            },
                                            {
                                                'label': '��������',
                                                'action': 'message',
                                                'messageText': '��������'
                                            },
                                            {
                                                'label': 'ó������',
                                                'action': 'message',
                                                'messageText': 'ó������'
                                            }
                                        ]
                                    }
                                })

                            # ������ ���� ȹ�� ����
                            else:
                                # response
                                return JsonResponse({
                                    'version': "2.0",
                                    'template': {
                                        'outputs': [{
                                            'simpleText': {
                                                'text': "������ ������ Ȯ���� �� �����ϴ�!!"
                                            }
                                        }],
                                        'quickReplies': [
                                            {
                                                'label': '��������',
                                                'action': 'message',
                                                'messageText': '��������'
                                            },
                                            {
                                                'label': 'ó������',
                                                'action': 'message',
                                                'messageText': 'ó������'
                                            }
                                        ]
                                    }
                                })

                    # �̹����� �Է����� ���� ����
                    except:
                        # �ٽ� �õ�
                        return regame()

            # -------------------
            # ������ ���� ȹ�� ����
            # -------------------
            if user.status == 12:
                if return_str == "��":
                    # DB ����
                    user.b_choice = "��"
                    user.status = 4  # --> �ùٸ� �������� Ȯ�� �Ϸ�, ������ ���� ���� ����
                    user.save()
                    return_str=user.cidesc # return_str�� description���� �����ϰ� ������ ���� ���� �������� �̵�

                # '�ƴϿ�'�� ������ ó��

                # �̻��� ��ȭ
                else:
                    # �ٽ� �õ�
                    return regame()

            # -------------
            # �з� ���� ����
            # -------------
            if user.status == 1 or (user.status == 2 and return_str == "�ٽ� �õ�") or ((user.status == 2.5 or user.status == 3) and return_str == "��������"):
                # <Ư�� ���̽�> �з� ���� -> ǰ�� ���� �� �ùٸ��� ���� �Է� -> �ٽ� �õ�
                # <Ư�� ���̽�> �з� ���� -> ǰ�� ���� -> �� ���� �� "��������"
                if (user.status == 2 and return_str == "�ٽ� �õ�") or ((user.status == 2.5 or user.status == 3) and return_str == "��������"):
                    return_str=user.citype

                # �з� ������ IT ��ųʸ� Ű�� ���� or '��Ÿ'
                if (return_str in IT) or (return_str == "��Ÿ"):
                    # DB ����
                    type = return_str
                    user.citype = type
                    user.status = 2  # --> �з� ���� �Ϸ�, ǰ�� ���� ����
                    user.save()

                    # response (��Ÿ)
                    if return_str == "��Ÿ":
                        return JsonResponse({
                            'version': "2.0",
                            'template': {
                                'outputs': [{
                                    'simpleText': {
                                        'text': "ǰ���� ���� �Է����ּ���!!"
                                    }
                                }],
                                'quickReplies': [
                                    {
                                        'label': '��������',
                                        'action': 'message',
                                        'messageText': '��������'
                                    },
                                    {
                                        'label': 'ó������',
                                        'action': 'message',
                                        'messageText': 'ó������'
                                    }
                                ]
                            }
                        })

                    # response (ǰ�� ����)
                    if return_str in IT:
                        return JsonResponse({
                            'version': "2.0",
                            'template': {
                                'outputs': [{
                                    'simpleText': {
                                        'text': "������ ǰ���� �������ּ���!!"
                                    }
                                }],
                                'quickReplies': [
                                    {
                                        'label': IT[type][0],
                                        'action': 'message',
                                        'messageText': IT[type][0]
                                    },
                                    {
                                        'label': IT[type][1],
                                        'action': 'message',
                                        'messageText': IT[type][1]
                                    },
                                    {
                                        'label': IT[type][2],
                                        'action': 'message',
                                        'messageText': IT[type][2]
                                    },
                                    {
                                        'label': IT[type][3],
                                        'action': 'message',
                                        'messageText': IT[type][3]
                                    },
                                    {
                                        'label': IT[type][4],
                                        'action': 'message',
                                        'messageText': IT[type][4]
                                    },
                                    {
                                        'label': IT[type][5],
                                        'action': 'message',
                                        'messageText': IT[type][5]
                                    },
                                    {
                                        'label': IT[type][6],
                                        'action': 'message',
                                        'messageText': IT[type][6]
                                    },
                                    {
                                        'label': '��������',
                                        'action': 'message',
                                        'messageText': '��������'
                                    },
                                    {
                                        'label': 'ó������',
                                        'action': 'message',
                                        'messageText': 'ó������'
                                    }
                                ]
                            }
                        })

                # �з� ������ IT ��ųʸ� Ű�� �������� ���� or '��Ÿ'�� �ƴ�
                else:
                    # �ٽ� �õ�
                    return regame()

            # -------------------
            # ǰ�� '���� �Է�' ����
            # -------------------
            if user.status == 2:
                # ǰ�� ������ '���� �Է�'�� ���
                if return_str == "���� �Է�":
                    # DB ����
                    user.status = 2.5  # --> ǰ�� '���� �Է�' ����, ǰ�� �Է� ����
                    user.save()

                    return JsonResponse({
                        'version': "2.0",
                        'template': {
                            'outputs': [{
                                'simpleText': {
                                    'text': "ǰ���� �Է����ּ���!!"
                                }
                            }],
                            'quickReplies': [
                                {
                                    'label': '��������',
                                    'action': 'message',
                                    'messageText': '��������'
                                },
                                {
                                    'label': 'ó������',
                                    'action': 'message',
                                    'messageText': 'ó������'
                                }
                            ]
                        }
                    })

            # -----------------
            # ǰ�� ���� �Է� ����
            # -----------------
            if user.status == 2.5:
                # DB ����
                name = return_str
                user.ciname = name
                user.status = 3  # --> ǰ�� ���� �Ϸ�, �� ���� ����
                user.save()

                # return
                return JsonResponse({
                    'version': "2.0",
                    'template': {
                        'outputs': [{
                            'simpleText': {
                                'text': '�������� �� ������ �Է��Ͻðڽ��ϱ�?'
                            }
                        }],
                        'quickReplies': [
                            {
                                'label': '��',
                                'action': 'message',
                                'messageText': '��'
                            },
                            {
                                'label': '�ƴϿ�',
                                'action': 'message',
                                'messageText': '�ƴϿ�'
                            },
                            {
                                'label': '��������',
                                'action': 'message',
                                'messageText': '��������'
                            },
                            {
                                'label': 'ó������',
                                'action': 'message',
                                'messageText': 'ó������'
                            }
                        ]
                    }
                })

            # -------------
            # ǰ�� ���� ����
            # -------------
            if user.status == 2 or (user.status == 3 and return_str == "�ٽ� �õ�") or (user.status == 4 and return_str == "��������") or (user.status == 5 and user.d_choice == "�ƴϿ�" and return_str == "��������"):
                # <Ư�� ���̽�> �з� ���� -> ǰ�� ���� -> �� ���� �� �ùٸ��� ���� �Է� -> �ٽ� �õ�
                # <Ư�� ���̽�> �з� ���� -> ǰ�� ���� -> �� ����(��) -> �� ���� �Է� �� "��������"
                # <Ư�� ���̽�> �з� ���� -> ǰ�� ���� -> �� ����(�ƴϿ�) -> ���� �Է� �� "��������"
                if (user.status == 3 and return_str == "�ٽ� �õ�") or (user.status == 4 and return_str == "��������") or (user.status == 5 and user.d_choice == "�ƴϿ�" and return_str == "��������"):
                    return_str=user.ciname

                # ǰ�� ������ IT[type]�� ���� ex) '��'�� IT['�����']�� ���� or '��Ÿ'->����ڰ� �Է��� ǰ���� ���
                if (return_str in IT[user.citype]) or (user.citype=='��Ÿ'):
                    # DB ����
                    name = return_str
                    user.ciname = name
                    user.status = 3 # --> ǰ�� ���� �Ϸ�, �� ���� ����
                    user.save()

                    # return
                    return JsonResponse({
                        'version': "2.0",
                        'template': {
                            'outputs': [{
                                'simpleText': {
                                    'text': '�������� �� ������ �Է��Ͻðڽ��ϱ�?'
                                }
                            }],
                            'quickReplies': [
                                {
                                    'label': '��',
                                    'action': 'message',
                                    'messageText': '��'
                                },
                                {
                                    'label': '�ƴϿ�',
                                    'action': 'message',
                                    'messageText': '�ƴϿ�'
                                },
                                {
                                    'label': '��������',
                                    'action': 'message',
                                    'messageText': '��������'
                                },
                                {
                                    'label': 'ó������',
                                    'action': 'message',
                                    'messageText': 'ó������'
                                }
                            ]
                        }
                    })

                # ǰ�� ������ IT[type]�� �������� ����
                else:
                    # �ٽ� �õ�
                    return regame()

            # ----------------
            # �� ���� ���� ����
            # ----------------
            if user.status == 3 or (user.status == 5 and user.d_choice == "��" and return_str == "��������"):
                # <Ư�� ���̽�> �з� ���� -> ǰ�� ���� -> �� ���� -> �� ���� �Է�(��) -> ���� �Է� �� "��������"
                if user.status == 5 and user.d_choice == "��" and return_str == "��������":
                    return_str=user.d_choice

                # �ùٸ� �� ���� ����
                if return_str == "��" or return_str == "�ƴϿ�":
                    # DB ����
                    choice = return_str
                    user.d_choice = choice
                    user.status = 4 # --> �� ���� �Ϸ�, �� ���� �Է� ����
                    user.save()

                    if return_str == "��":
                        # return
                        return JsonResponse({
                            'version': "2.0",
                            'template': {
                                'outputs': [{
                                    'simpleText': {
                                        'text': '�� ������ �Է����ּ���!!'
                                    }
                                }],
                                'quickReplies': [
                                    {
                                        'label': '��������',
                                        'action': 'message',
                                        'messageText': '��������'
                                    },
                                    {
                                        'label': 'ó������',
                                        'action': 'message',
                                        'messageText': 'ó������'
                                    }
                                ]
                            }
                        })

                # �ùٸ��� �ʴ� ����
                else:
                    # �ٽ� �õ�
                    return regame()

            # ----------------
            # �� ���� �Է� ����
            # ----------------
            if user.status == 4 or (user.status == 5 and return_str == "�ٽ� �õ�") or (user.status == 6 and return_str == "��������"):
                # <Ư�� ���̽�> �з� ���� -> ǰ�� ���� -> �� ���� -> �� ���� �Է� -> ���� �Է� �� �ùٸ��� ���� �Է� -> �ٽ� �õ�
                # <Ư�� ���̽�> �з� ���� -> ǰ�� ���� -> �� ���� -> �� ���� �Է� -> ���� �Է� -> ������� ��� ���� �� "��������"
                if (user.status == 5 and return_str == "�ٽ� �õ�") or (user.status == 6 and return_str == "��������"):
                    return_str=user.cidesc # return_str='x' or description

                # �� ������ �Է����� �ʾ� �� ���ǹ����� �Ѿ�� ���
                if return_str == "�ƴϿ�":
                    return_str="" # �� ����: ''

                # DB ����
                desc = return_str
                user.cidesc=desc
                user.status = 5  # --> �� ���� �Է� �Ϸ�, ���� �Է� ����
                user.save()

                # return
                return JsonResponse({
                    'version': "2.0",
                    'template': {
                        'outputs': [{
                            'simpleText': {
                                'text': "������ ������ �������ּ���!!\n\n(3�� �̻��̸� ���� ���� �Է�)"
                            }
                        }],
                        'quickReplies': [
                            {
                                'label': '1��',
                                'action': 'message',
                                'messageText': '1��'
                            },
                            {
                                'label': '2��',
                                'action': 'message',
                                'messageText': '2��'
                            },
                            {
                                'label': '��������',
                                'action': 'message',
                                'messageText': '��������'
                            },
                            {
                                'label': 'ó������',
                                'action': 'message',
                                'messageText': 'ó������'
                            }
                        ]
                    }
                })

            # -------------
            # ���� ���� ����
            # -------------
            if user.status == 5 or (user.status == 6 and return_str == "�ٽ� �õ�") or (user.status >= 7 and (return_str == "��������" or return_str == "����")):
                # <Ư�� ���̽�> �з� ���� -> ǰ�� ���� -> �� ���� -> �� ���� �Է� -> ���� �Է� -> ������� ��� ���� �� �ùٸ��� ���� �Է� -> �ٽ� �õ�
                # <Ư�� ���̽�> �з� ���� -> ǰ�� ���� -> �� ���� -> �� ���� �Է� -> ���� �Է� -> ������� ��� ���� -> ������� ó�� �� �߸��� �Է� -> �ٽ� �õ�
                # <Ư�� ���̽�> �з� ���� -> ǰ�� ���� -> �� ���� -> �� ���� �Է� -> ���� �Է� -> ������� ��� ���� -> ������� ó�� �� "��������"
                # <Ư�� ���̽�> �з� ���� -> ǰ�� ���� -> �� ���� -> �� ���� �Է� -> ���� �Է� -> ������� ��� ���� -> ������� ó�� �� "����"
                if (user.status == 6 and return_str == "�ٽ� �õ�") or (user.status >= 7 and (return_str == "��������" or return_str == "����")):
                    return_str=str(user.cinum) # return_str=str(num)
                    re=1
                else:
                    re=0

                # ����ڰ� ���� �Է��� ���
                try:
                    # �Էµ� ���� �ڿ� "��" �߰�
                    if return_str[-1] != "��":
                        return_str += "��"

                    # �ǹ��ִ� ��ġ�� ���
                    if int(return_str[0:-1]) > 0:
                        num = int(return_str[0:-1])

                        # DB ����
                        user.cinum = num
                        user.status = 6 # --> ���� �Է� �Ϸ�, ������� �Է� ��� ���� ����
                        user.save()

                        # �ٽ� �����ϴ� ���
                        if re==1:
                            txt="�ٽ� "
                        else:
                            txt=""

                        # response
                        return JsonResponse({
                            'version': "2.0",
                            'template': {
                                'outputs': [{
                                    'simpleText': {
                                        'text': '������� �Է� ����� '+txt+'�������ּ���!!'
                                    }
                                }],
                                'quickReplies': [
                                    {
                                        'label': '�̹��� ����',
                                        'action': 'message',
                                        'messageText': '�̹���'
                                    },
                                    {
                                        'label': '��¥ ����',
                                        'action': 'message',
                                        'messageText': '��¥'
                                    },
                                    {
                                        'label': '������� ����',
                                        'action': 'message',
                                        'messageText': '������� ����'
                                    },
                                    {
                                        'label': '��������',
                                        'action': 'message',
                                        'messageText': '��������'
                                    },
                                    {
                                        'label': 'ó������',
                                        'action': 'message',
                                        'messageText': 'ó������'
                                    }
                                ]
                            }
                        })

                    # �ǹ̾��� ��ġ�� ���
                    else:
                        # �ٽ� �õ�
                        return regame()

                # ����ڰ� ���� �Է����� ���� ���
                except:
                    # �ٽ� �õ�
                    return regame()

            # -------------------------
            # ������� �Է� ��� ���� ����
            # -------------------------
            if user.status == 6 or (user.status >= 7 and return_str == "�ٽ� �õ�"):
                # <Ư�� ���̽�> �з� ���� -> ǰ�� ���� -> �� ���� -> �� ���� �Է� -> ���� �Է� -> ������� ��� ����(�̹���) -> �̹��� ���� �� �� -> �ٽ� �õ�
                if user.status >= 7 and return_str == "�ٽ� �õ�":
                    return_str = "�̹���"

                # ��¥ ���� ���
                if return_str == "��¥":
                    # DB ����
                    user.status = 7  # --> ������� �Է� ��� ���� �Ϸ�, ��¥ ���� ����
                    user.save()

                    # ����� ��ȭ�� ��¥���� Ȯ��
                    try:
                        return_day=return_json_str['action']['detailParams']['date']['origin']
                        print(return_day)
                        if return_day:
                            print('day exist!!')
                            # DB ����
                            user.cidate=return_day
                            user.save()
                            newItem = models.Item(user=user, icode=user.cicode, itype=user.citype, iname=user.ciname, idesc=user.cidesc, inum=user.cinum, idate=user.cidate)
                            newItem.save()
                            user.cicode+=1
                            user.save()

                            # DB �ʱ�ȭ
                            init_db(user)

                            # response
                            return JsonResponse({
                                'version': "2.0",
                                'template': {
                                    'outputs': [{
                                        'simpleText': {
                                            'text': "������ ������ �Ϸ�Ǿ����ϴ�!!"
                                        }
                                    }],
                                    'quickReplies': [
                                        {
                                            'label': '����Ʈ Ȯ��',
                                            'action': 'message',
                                            'messageText': '����Ʈ Ȯ��'
                                        },
                                        {
                                            'label': '������ �߰�',
                                            'action': 'message',
                                            'messageText': '������ �߰�'
                                        },
                                        {
                                            'label': 'ó������',
                                            'action': 'message',
                                            'messageText': 'ó������'
                                        },
                                    ]
                                }
                            })

                    # ����� ��ȭ�� ��¥�� �ƴ� (����)
                    except:
                        # DB �ʱ�ȭ �� response
                        init_db(user)
                        return init_rs()

                # �̹��� ���� ���
                elif return_str == "�̹���":
                    # DB ����
                    user.status = 7  # --> ������� �Է� ��� ���� �Ϸ�, �̹��� ���� ����
                    user.save()

                    # response
                    return JsonResponse({
                        'version': "2.0",
                        'template': {
                            'outputs': [{
                                'simpleText': {
                                    'text': "��������� ���Ե� �̹����� �������ּ���. ���ڰ� �ʹ� ���ų� ȭ���� �� ���� �̹����� �νķ��� �������ϴ�.\n\n(����) 5�� �̻� ������ ������ '��������'�� �Է��ؼ� �ٽ� �õ����ּ���!!"
                                }
                            }],
                            'quickReplies': [
                                {
                                    'label': '��������',
                                    'action': 'message',
                                    'messageText': '��������'
                                },
                                {
                                    'label': 'ó������',
                                    'action': 'message',
                                    'messageText': 'ó������'
                                }
                            ]
                        }
                    })

                # ������� ����
                elif return_str == "������� ����":
                    # DB ����
                    user.status = 7  # --> ������� �Է� ��� ���� �Ϸ�, �����ϰ� ������ ����
                    user.save()

                    # �̻�ġ ���� ('DB2ImageUrl'�Լ����� ó����)
                    newItem = models.Item(user=user, icode=user.cicode, itype=user.citype, iname=user.ciname,
                                          idesc=user.cidesc, inum=user.cinum, idate="2099-12-31")
                    newItem.save()
                    user.cicode += 1
                    user.save()

                    # DB �ʱ�ȭ
                    init_db(user)

                    # response
                    return JsonResponse({
                        'version': "2.0",
                        'template': {
                            'outputs': [{
                                'simpleText': {
                                    'text': "������ ������ �Ϸ�Ǿ����ϴ�!!"
                                }
                            }],
                            'quickReplies': [
                                {
                                    'label': '����Ʈ Ȯ��',
                                    'action': 'message',
                                    'messageText': '����Ʈ Ȯ��'
                                },
                                {
                                    'label': '������ �߰�',
                                    'action': 'message',
                                    'messageText': '������ �߰�'
                                },
                                {
                                    'label': 'ó������',
                                    'action': 'message',
                                    'messageText': 'ó������'
                                },
                            ]
                        }
                    })

                # �ǹ̾��� �Է��� ���
                else:
                    # �ٽ� �õ�
                    return regame()

            # --------------------------
            # OCR ó���� �̹��� ���� ����
            # --------------------------
            if user.status == 7:
                # ����� ��ȭ�� �������� Ȯ��
                try:
                    return_img = return_json_str['userRequest']['params']['media']['url']
                    print(return_img)

                    # ������ ���� ��
                    if return_img:
                        # DB ����
                        user.status = 8  # --> �̹��� ���� �Ϸ�, ������� ���� ����
                        user.save()

                        # =================================================
                        # OCR �ڵ�
                        # 1. īī�� �̹��� URL�� cv2 �̹����� ��ȯ�Ѵ�.
                        # 2. YOLOv5 ���۷����� ���� ������� �̹����� ��´�.
                        # 3. ����ó���� ���� ������� �̹����� �����Ѵ�.
                        # 4. ���� OCR�� �ؽ�Ʈ�� ã�´�.
                        # 5. �ؽ�Ʈ�� ��¥ �������� ��ȯ�Ѵ�.
                        # =================================================
                        ocr_result = 0
                        org_img = fp_ip.url2img(return_img)  # (1)
                        s, img = fp_ip.inference(org_img)  # (2)

                        # YOLOv5 Inference���� �ùٸ��� ã��
                        if s == 1:
                            pre_img = fp_ip.image_change(img)  # (3)
                            ocr_list = fp_ip.detectText(pre_img)  # (4)
                            # ���� OCR API���� �ùٸ��� ã��
                            if len(ocr_list) >= 2:
                                ocr_result = fp_ip.result_word(ocr_list)  # (5)
                            print(ocr_result)

                            # ó���� �̹��� �� �����ʹ� ����
                            del img
                            del pre_img
                            del ocr_list

                        # �ùٸ� ��¥�� ��ȯ�� ���
                        if ocr_result != 0:
                            # make list and sorting
                            ocr_result=list(ocr_result)
                            ocr_result.sort()
                            # split
                            size = len(ocr_result)
                            dates = [[0 for col in range(3)] for row in range(size)]
                            for i in range(size):
                                year, month, date = fp_ip.ocr_split(ocr_result[i])
                                dates[i][0] = year
                                dates[i][1] = month
                                dates[i][2] = date

                            # response
                            if size == 1:
                                return response_select.one(dates,ocr_result)
                            elif size == 2:
                                return response_select.two(dates,ocr_result)
                            elif size == 3:
                                return response_select.three(dates,ocr_result)
                            elif size == 4:
                                return response_select.four(dates,ocr_result)
                            elif size == 5:
                                return response_select.five(dates,ocr_result)
                            elif size == 6:
                                return response_select.six(dates,ocr_result)
                            elif size == 7:
                                return response_select.seven(dates,ocr_result)
                            elif size == 8:
                                return response_select.eight(dates,ocr_result)
                            elif size == 9:
                                return response_select.nine(dates,ocr_result)
                            else:
                                return response_select.ten(dates,ocr_result)

                        # �ùٸ� ��¥�� ��ȯ���� ���� ���
                        else:
                            print('ocr fail')
                            # response
                            return JsonResponse({
                                'version': "2.0",
                                'template': {
                                    'outputs': [{
                                        'simpleText': {
                                            'text': "��������� Ȯ���� �� �����ϴ�!!"
                                        }
                                    }],
                                    'quickReplies': [
                                        {
                                            'label': '��������',
                                            'action': 'message',
                                            'messageText': '��������'
                                        },
                                        {
                                            'label': 'ó������',
                                            'action': 'message',
                                            'messageText': 'ó������'
                                        }
                                    ]
                                }
                            })

                # ����� ��ȭ�� ������ �ƴ�
                except:
                    # �ٽ� �õ�
                    return regame()


            # --------------------------
            # OCR�� ���� ������� ���� ����
            # --------------------------
            if user.status == 8:
                # ��������� ���������� try���� ���� �۵���
                try:
                    # DB ����
                    user.cidate = return_str
                    user.save()
                    newItem = models.Item(user=user, icode=user.cicode, itype=user.citype, iname=user.ciname,
                                          idesc=user.cidesc, inum=user.cinum, idate=user.cidate)
                    newItem.save()
                    user.cicode += 1
                    user.save()

                    # DB �ʱ�ȭ
                    init_db(user)

                    # response
                    return JsonResponse({
                        'version': "2.0",
                        'template': {
                            'outputs': [{
                                'simpleText': {
                                    'text': "������ ������ �Ϸ�Ǿ����ϴ�!!"
                                }
                            }],
                            'quickReplies': [
                                {
                                    'label': '����Ʈ Ȯ��',
                                    'action': 'message',
                                    'messageText': '����Ʈ Ȯ��'
                                },
                                {
                                    'label': '������ �߰�',
                                    'action': 'message',
                                    'messageText': '������ �߰�'
                                },
                                {
                                    'label': 'ó������',
                                    'action': 'message',
                                    'messageText': 'ó������'
                                },
                            ]
                        }
                    })

                # ��������� �������� ����
                except:
                    # �ٽ� �õ� (�̹��� �Էº���)
                    return regame()


        # =================================================
        # �޴�2 ('����Ʈ Ȯ��' ��ȭ ����)
        # =================================================

        if user.menu == 2:
            # ---------------
            # ItemDB ���� Ȯ��
            # ---------------
            table = models.Item.objects.filter(user=userId).order_by('idate')
            if table.exists():
                pass
            else:
                table = 0

            # ������ �����Ͱ� ���� x
            if table == 0:
                # DB �ʱ�ȭ
                init_db(user)

                # response
                return JsonResponse({
                    'version': "2.0",
                    'template': {
                        'outputs': [{
                            'simpleText': {
                                'text': "����� �����Ͱ� �����ϴ�!"
                            }
                        }],
                        'quickReplies': [{
                            'label': 'ó������',
                            'action': 'message',
                            'messageText': 'ó������'
                        }]
                    }
                })

            # -------------
            # �޴� ���� ����
            # -------------
            if user.status == 0:
                # DB ����
                user.status = 1  # --> �޴� ���� �Ϸ�, ����Ʈ ����
                user.save()

                # DB -> Image url
                _url = DB2ImageUrl(table, userId, user.menu)

                # DB �ʱ�ȭ <�޴�1�� �� �� �ֵ���>
                init_db(user)

                # response
                return JsonResponse({
                    'version': "2.0",
                    'template': {
                        'outputs': [{
                            'simpleImage': {
                                "imageUrl": _url,
                                "altText": "���̺�"
                            }
                        }],
                        'quickReplies': [
                            {
                                'label': '������ �߰�',
                                'action': 'message',
                                'messageText': '������ �߰�'
                            },
                            {
                                'label': 'ó������',
                                'action': 'message',
                                'messageText': 'ó������'
                            }
                        ]
                    }
                })


        # =================================================
        # �޴�3 ('������ ����' ��ȭ ����)
        # =================================================

        if user.menu == 3:
            # ---------------
            # ItemDB ���� Ȯ��
            # ---------------
            table = models.Item.objects.filter(user=userId).order_by('idate')
            if table.exists():
                pass
            else:
                table = 0

            # ������ �����Ͱ� ���� x
            if table == 0:
                # DB �ʱ�ȭ
                init_db(user)

                # response
                return JsonResponse({
                    'version': "2.0",
                    'template': {
                        'outputs': [{
                            'simpleText': {
                                'text': "����� �����Ͱ� �����ϴ�!"
                            }
                        }],
                        'quickReplies': [{
                            'label': 'ó������',
                            'action': 'message',
                            'messageText': 'ó������'
                        }]
                    }
                })

            # -------------
            # �޴� ���� ����
            # -------------
            if user.status == 0 or ((user.status == 1 or user.status == 2) and return_str == "�ٽ� �õ�") or ((user.status >= 2 or user.status <= 4) and return_str == "��������"):
                # DB ����
                user.status = 1  # --> �޴� ���� �Ϸ�, '����� ������ Ȯ��', '����� ������ ����', '�� ���� ����' ���� ����
                user.save()

                # response
                return JsonResponse({
                    'version': "2.0",
                    'template': {
                        'outputs': [{
                            'simpleText': {
                                'text': "1. ��������� ����� �������� �� ���� ������ �� �ֽ��ϴ�!\n\n2. �ڵ带 �Է��ؼ� �������� �� ���� ������ �� �ֽ��ϴ�!"
                            }
                        }],
                        'quickReplies': [
                            {
                                'label': '����� ������ Ȯ��',
                                'action': 'message',
                                'messageText': '����� ������ Ȯ��'
                            },
                            {
                                'label': '����� ������ ����',
                                'action': 'message',
                                'messageText': '����� ������ ����'
                            },
                            {
                                'label': '�� ���� ����',
                                'action': 'message',
                                'messageText': '�� ���� ����'
                            },
                            {
                                'label': 'ó������',
                                'action': 'message',
                                'messageText': 'ó������'
                            }
                        ]
                    }
                })

            # ------------------------------------
            # '����� ������' or '�� ���� ����' ���� �Ϸ�
            # ------------------------------------
            if user.status == 1 or ((user.status == 3 or user.status == 4) and return_str == "�ٽ� �õ�"):
                if return_str == "����� ������ Ȯ��" or return_str == "����� ������ ����":
                    # DB ����
                    user.status = 2  # --> (1) '����� ������ Ȯ��' or (2) '����� ������ ����' ���� �Ϸ�, ���� ������ Ȯ�� �� ����
                    user.save()

                elif return_str == "�� ���� ����" or ((user.status == 3 or user.status == 4) and return_str == "�ٽ� �õ�"):
                    # DB ����
                    user.status = 3 # --> (3) '�� ���� ����' ���� �Ϸ�, '�ڵ� Ȯ��' �Է� or �ڵ� �Է� ����
                    user.save()

                    # response
                    return JsonResponse({
                        'version': "2.0",
                        'template': {
                            'outputs': [{
                                'simpleText': {
                                    'text': "�ڵ带 �Է��ϸ� �ش� �������� �����˴ϴ�!\n\nex) '3' �Է�\n(�ڵ带 �𸣸� '�ڵ� Ȯ��' �� ����!)"
                                }
                            }],
                            'quickReplies': [
                                {
                                    'label': '�ڵ� Ȯ��',
                                    'action': 'message',
                                    'messageText': '�ڵ� Ȯ��'
                                },
                                {
                                    'label': '��������',
                                    'action': 'message',
                                    'messageText': '��������'
                                },
                                {
                                    'label': 'ó������',
                                    'action': 'message',
                                    'messageText': 'ó������'
                                }
                            ]
                        }
                    })

                else:
                    # �ٽ� �õ�
                    return regame()



            # ---------------------------------
            # ����� ������ Ȯ��/���� ���� ����
            # ---------------------------------
            if user.status == 2:
                if return_str == "����� ������ Ȯ��":
                    # ����� ������ѿ� ���� ���̺� ����
                    dt_now = datetime.datetime.now()
                    today = dt_now.date()
                    end_table = models.Item.objects.filter(user=userId, idate__lt=today).order_by('idate')  # __lt: <

                    # ����� �������� ������ ������
                    if end_table.exists():
                        # DB -> Image url
                        _url = DB2ImageUrl(end_table, userId, user.menu)

                        # response
                        return JsonResponse({
                            'version': "2.0",
                            'template': {
                                'outputs': [{
                                    'simpleImage': {
                                        "imageUrl": _url,
                                        "altText": "���̺�"
                                    }
                                }],
                                'quickReplies': [
                                    {
                                        'label': '����� ������ ����',
                                        'action': 'message',
                                        'messageText': '����� ������ ����'
                                    },
                                    {
                                        'label': '��������',
                                        'action': 'message',
                                        'messageText': '��������'
                                    },
                                    {
                                        'label': 'ó������',
                                        'action': 'message',
                                        'messageText': 'ó������'
                                    }
                                ]
                            }
                        })

                    # ����� �������� ����
                    else:
                        # response
                        return JsonResponse({
                            'version': "2.0",
                            'template': {
                                'outputs': [{
                                    'simpleText': {
                                        'text': "����� �������� �����ϴ�!"
                                    }
                                }],
                                'quickReplies': [{
                                    'label': '��������',
                                    'action': 'message',
                                    'messageText': '��������'
                                },{
                                    'label': 'ó������',
                                    'action': 'message',
                                    'messageText': 'ó������'
                                }]
                            }
                        })

                elif return_str == "����� ������ ����":
                    # ����� ������ѿ� ���� ���̺�� ����
                    dt_now = datetime.datetime.now()
                    today = dt_now.date()
                    end_table = models.Item.objects.filter(user=userId, idate__lt=today).order_by('idate')  # __lt: <

                    # ����� �������� ������ ����
                    if end_table.exists():
                        # delete
                        end_table.delete()
                        # response
                        return JsonResponse({
                            'version': "2.0",
                            'template': {
                                'outputs': [{
                                    'simpleText': {
                                        'text': "����� ������(��)�� �����Ǿ����ϴ�!!"
                                    }
                                }],
                                'quickReplies': [
                                    {
                                        'label': '����� ����Ʈ Ȯ��',
                                        'action': 'message',
                                        'messageText': '����� ����Ʈ Ȯ��'
                                    },
                                    {
                                        'label': '��������',
                                        'action': 'message',
                                        'messageText': '��������'
                                    },
                                    {
                                        'label': 'ó������',
                                        'action': 'message',
                                        'messageText': 'ó������'
                                    }
                                ]
                            }
                        })

                    # ����� �������� ����
                    else:
                        # response
                        return JsonResponse({
                            'version': "2.0",
                            'template': {
                                'outputs': [{
                                    'simpleText': {
                                        'text': "����� �������� �����ϴ�!"
                                    }
                                }],
                                'quickReplies': [{
                                    'label': '��������',
                                    'action': 'message',
                                    'messageText': '��������'
                                }, {
                                    'label': 'ó������',
                                    'action': 'message',
                                    'messageText': 'ó������'
                                }]
                            }
                        })

                # �Ϲ� ����Ʈ ��ȯ
                elif return_str == "����� ����Ʈ Ȯ��":
                    # DB -> Image url
                    _url = DB2ImageUrl(table, userId, user.menu)

                    # response
                    return JsonResponse({
                        'version': "2.0",
                        'template': {
                            'outputs': [{
                                'simpleImage': {
                                    "imageUrl": _url,
                                    "altText": "���̺�"
                                }
                            }],
                            'quickReplies': [
                                {
                                    'label': '��������',
                                    'action': 'message',
                                    'messageText': '��������'
                                },
                                {
                                    'label': 'ó������',
                                    'action': 'message',
                                    'messageText': 'ó������'
                                }
                            ]
                        }
                    })

                # �̻��� ��ȭ
                else:
                    # �ٽ� �õ�
                    return regame()


            # -------------------------------
            # �ڵ� �Է� or '�ڵ� Ȯ��' �Է� ����
            # -------------------------------
            if user.status >= 3:
                # '�ڵ� Ȯ��' or '����� ����Ʈ Ȯ��' ��ȭ ó��
                if (return_str == "�ڵ� Ȯ��") or (return_str == "����� ����Ʈ Ȯ��"):
                    # DB ����
                    user.status = 4  # --> '�ڵ� Ȯ��' �Ϸ�, ����Ʈ ����
                    user.save()

                    # DB -> Image url
                    _url = DB2ImageUrl(table,userId,user.menu)

                    # response
                    return JsonResponse({
                        'version': "2.0",
                        'template': {
                            'outputs': [{
                                'simpleImage': {
                                    "imageUrl": _url,
                                    "altText": "���̺�"
                                }
                            }],
                            'quickReplies': [
                                {
                                    'label': '��������',
                                    'action': 'message',
                                    'messageText': '��������'
                                },
                                {
                                    'label': 'ó������',
                                    'action': 'message',
                                    'messageText': 'ó������'
                                }
                            ]
                        }
                    })

                # ������ �ڵ�� ����Ʈ ������ ���� (DB ���ڵ� ����), ����
                else:
                    # ������ �ڵ尡 �Է����� �Դ��� Ȯ��
                    try:
                        code = int(return_str)
                        # ��ȿ�� �ڵ����� Ȯ�� (����� ID�� ������ CODE�� ������ ���ڵ� ã��)
                        record = models.Item.objects.get(user=userId, icode=code)

                        if record:
                            # DB ����
                            user.status = 4  # --> �ڵ� �Է� �Ϸ�, �ڵ忡 �ش�Ǵ� ���ڵ� ����
                            user.save()

                            # ������ �������� ǰ��
                            name = str(record.iname)
                            # delete
                            record.delete()
                            # response
                            return JsonResponse({
                                'version': "2.0",
                                'template': {
                                    'outputs': [{
                                        'simpleText': {
                                            'text': str(code) + "�� ������("+name+")�� �����Ǿ����ϴ�!!\n\n�ڵ� �Է� �� �߰� ������ �����մϴ�!"
                                        }
                                    }],
                                    'quickReplies': [
                                        {
                                            'label': '����� ����Ʈ Ȯ��',
                                            'action': 'message',
                                            'messageText': '����� ����Ʈ Ȯ��'
                                        },
                                        {
                                            'label': '��������',
                                            'action': 'message',
                                            'messageText': '��������'
                                        },
                                        {
                                            'label': 'ó������',
                                            'action': 'message',
                                            'messageText': 'ó������'
                                        }
                                    ]
                                }
                            })

                        # ����
                        else:
                            # �ٽ� �õ�
                            return JsonResponse({
                                'version': "2.0",
                                'template': {
                                    'outputs': [{
                                        'simpleText': {
                                            'text': '��ȿ���� ���� �ڵ��Դϴ�. �ٽ� �õ����ּ���.'
                                        }
                                    }],
                                    'quickReplies': [
                                        {
                                            'label': '�ٽ� �õ�',
                                            'action': 'message',
                                            'messageText': '�ٽ� �õ�'
                                        },
                                        {
                                            'label': 'ó������',
                                            'action': 'message',
                                            'messageText': 'ó������'
                                        }
                                    ]
                                }
                            })

                    # ��ȿ���� ���� �ڵ�
                    except:
                        # �ٽ� �õ�
                        return JsonResponse({
                            'version': "2.0",
                            'template': {
                                'outputs': [{
                                    'simpleText': {
                                        'text': '��ȿ���� ���� �ڵ��Դϴ�. �ٽ� �õ����ּ���.'
                                    }
                                }],
                                'quickReplies': [
                                    {
                                        'label': '�ٽ� �õ�',
                                        'action': 'message',
                                        'messageText': '�ٽ� �õ�'
                                    },
                                    {
                                        'label': 'ó������',
                                        'action': 'message',
                                        'messageText': 'ó������'
                                    }
                                ]
                            }
                        })


        # =================================================
        # �޴�4 ('ȸ�� Ż��' ��ȭ ����)
        # =================================================

        if user.menu == 4:
            # -------------
            # �޴� ���� ����
            # -------------
            if user.status == 0 or (user.status==1 and return_str=="�ٽ� �õ�"):
                # DB ����
                user.status = 1  # --> �޴� ���� �Ϸ�, Ż�� ���� �ǹ��� ����
                user.save()

                # response
                return JsonResponse({
                    'version': "2.0",
                    'template': {
                        'outputs': [{
                            'simpleText': {
                                'text': "ȸ�� Ż�� �� ��� �����Ͱ� �����˴ϴ�.\n\n���� Ż���Ͻðڽ��ϱ�?"
                            }
                        }],
                        'quickReplies': [
                            {
                                'label': '��',
                                'action': 'message',
                                'messageText': '��'
                            },
                            {
                                'label': '�ƴϿ�',
                                'action': 'message',
                                'messageText': '�ƴϿ�'
                            }
                        ]
                    }
                })

            # -----------------
            # Ż�� ���� ���� ����
            # -----------------
            if user.status == 1:
                # Ż���Ѵٰ� ��
                if return_str == "��":
                    # DB ����
                    user.status = 2  # --> Ż�� ���� ���� �Ϸ�, Ż�� ó�� ����
                    user.save()

                    # ����
                    user.delete()

                    # response
                    return JsonResponse({
                        'version': "2.0",
                        'template': {
                            'outputs': [{
                                'simpleText': {
                                    'text': "Ż�� �Ϸ�Ǿ����ϴ�!"
                                }
                            }]
                        }
                    })

                # Ż������ �ʴ´ٰ� ��
                elif return_str == "�ƴϿ�":
                    # DB ����
                    user.status = 2  # --> Ż�� ���� ���� �Ϸ�, Ż�� ��� ó�� ����
                    user.save()

                    # DB �ʱ�ȭ
                    init_db(user)

                    # response
                    return JsonResponse({
                        'version': "2.0",
                        'template': {
                            'outputs': [{
                                'simpleText': {
                                    'text': "Ż�� ��ҵǾ����ϴ�!"
                                }
                            }],
                            'quickReplies': [
                                {
                                    'label': 'ó������',
                                    'action': 'message',
                                    'messageText': 'ó������'
                                }
                            ]
                        }
                    })

                # ����
                else:
                    # �ٽ� �õ�
                   return regame()

        # =================================================
        # < �޴� ���� �ڵ� �� >
        # =================================================

        # �������� �θ� �͵� �ƴϰ� Ż�� �ƴϰ� �޴��� �ƴ� ��ȭ
        else:
            # DB �ʱ�ȭ �� response
            init_db(user)
            return init_rs()


    # ��ϵ��� ���� ȸ���� ���
    else:
        # ȸ������
        if (return_str == "��������") or (return_str == "������") or (return_str == "��"):
            new=models.User(id=userId)
            new.save()
            return JsonResponse({
                'version': "2.0",
                'template': {
                    'outputs': [{
                        'simpleText': {
                            'text': "ȸ������ �Ϸ�!!\n�������� �ٽ� �θ��� �̿����ּ���!"
                        }
                    }],
                    'quickReplies': [{
                        'label': '������~!',
                        'action': 'message',
                        'messageText': '������'
                    }]
                }
            })

        # ȸ������ ����
        else:
            return JsonResponse({
                'version': "2.0",
                'template': {
                    'outputs': [{
                        'simpleText': {
                            'text': "��ϵ��� ���� ������Դϴ�. '������'�� �ҷ� ����� ����� ���ּ���!! \n\nex) '������' ����"
                        }
                    }]
                }
            })





