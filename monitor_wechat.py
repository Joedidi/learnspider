#!/usr/bin/env python
# -*- coding:utf-8 -*-
import traceback
"""
@author: Jamin Chen
@date:  2019/5/15 12:42
@explain:
@file: monitor_wechat.py
"""

import itchat
from itchat.content import TEXT
from itchat.content import *
import sys
import time
import importlib
import datetime
import re
importlib.reload(sys)
import threading
import pymysql
from pymongo import MongoClient




conn = MongoClient('localhost', 27017)
db = conn.mydb  #连接mydb数据库，没有则自动创建
my_set = db.wechat_set  #使用test_set集合，没有则自动创建


msg_information = {}
face_bug = None  # 针对表情包的内容
FromUserName='@@6adb4b85dd5e78f2630465f7821e3856f96d7eaf942ad5f90fdcc816981a166c'

@itchat.msg_register([NOTE,
                      TEXT,],
                     isFriendChat=False,
                     isGroupChat=True,
                     isMpChat=False)
def handle_receive_msg(msg):
    try:
        print(msg)
        if msg['FromUserName'] == FromUserName:
            print(msg)
            my_set.insert_one(msg)

    except BaseException:
        traceback.print_exc()



@itchat.msg_register(
    NOTE,
    isFriendChat=False,
    isGroupChat=True,
    isMpChat=False)
def information(msg):
    # 这里如果这里的msg['Content']中包含消息撤回和id，就执行下面的语句
    print(msg)
    try:
        if msg['FromUserName']==FromUserName:
            print(msg)
            # RoomList=msg['User']
            # User_list = RoomList['MemberList']
            # for User in User_list:
            #     member_num = User['UserName']
            #     member_name = User['NickName']
            #     Updata_member(member_num, member_name)
            if '邀请' in msg['Content']:
                Text = msg['Text']
                Inviter = change_emoji(re.match(r'\"(.*?)\"邀请"(.*?)\"加入', Text).group(1).strip())
                Invitee = change_emoji(re.match(r'\"(.*?)\"邀请\"(.*?)\"加入', Text).group(2).strip())
                dic={'msg_id':msg['MsgId'],'Inviter':Inviter,'Invitee':Invitee,'Invitation_time':datetime.datetime.now(),'mode':'邀请','group_num':FromUserName}
                IntoMysql_Invite(dic)

            if '通过扫描' in msg['Content']:
                Text = msg['Text']
                Invitee = change_emoji(re.match(r'\"(.*?)\"通过扫描"(.*?)\"分享', Text).group(1).strip())
                Inviter = change_emoji(re.match(r'\"(.*?)\"通过扫描\"(.*?)\"分享', Text).group(2).strip())
                dic = {'msg_id':msg['MsgId'],'Inviter': Inviter, 'Invitee': Invitee, 'Invitation_time': datetime.datetime.now(), 'mode': '扫描','group_num':FromUserName}
                IntoMysql_Invite(dic)
    except:
        traceback.print_exc()

def change_emoji(name):
    if 'emoji' in name:
        # name='<span class="emoji emoji1f484"></span>'
        spanlist=re.findall(r'<span class="(.*?)"></span>',name)
        print(spanlist)
        for span in spanlist:
            data=re.match('emoji(.*?)ji(.*)',span).group(2).strip()
            text=(r'\U000{0}'.format(data)).encode(encoding='utf8').decode('unicode-escape')
            name=name.replace('<span class="'+span+'"></span>',text)
    return name



def db_mysql():
    mysql_host = '192.168.36.38'
    mysql_db = 'qfn_pretreatment'
    mysql_user = 'root'
    mysql_password = '123456'
    mysql_port = 3306
    db = pymysql.connect(host=mysql_host, port=mysql_port, user=mysql_user, password=mysql_password, db=mysql_db,
                         charset='utf8mb4')  # 连接数据库编码注意是utf8，不然中文结果输出会乱码
    return db

def IntoMysql_Invite(dic):
    db = db_mysql()
    cursor = db.cursor()
    sqlExit = "SELECT *FROM wechat_group_invite_copy1 WHERE msg_id = '%s'" % dic['msg_id']
    res = cursor.execute(sqlExit)
    if res:
        return
    try:
        cols = ','.join(map(str, dic.keys()))
        values = '\',\''.join(map(str, dic.values()))
        sql = "INSERT INTO wechat_group_invite_copy1 (%s) VALUES (%s)" % (cols,  '\''+ values + '\'' )
        cursor.execute(sql)
        db.commit()
        db.close()
    except pymysql.Error as e:
        print("数据库错误，原因%d: %s" % (e.args[0], e.args[1]))



def IntoMysql_action(dic):
    db = db_mysql()
    cursor = db.cursor()
    sqlExit = "SELECT *FROM wechat_group_action_copy1 WHERE member_num = '%s'" % dic['member_num']
    res = cursor.execute(sqlExit)
    if res:
        return
    try:
        cols = ','.join(map(str, dic.keys()))
        values = '\',\''.join(map(str, dic.values()))
        sql = "INSERT INTO wechat_group_action_copy1 (%s) VALUES (%s)" % (cols,  '\''+ values + '\'' )
        cursor.execute(sql)
        db.commit()
        db.close()
    except pymysql.Error as e:
        print("数据库错误，原因%d: %s" % (e.args[0], e.args[1]))

def SelectMysql():
    db = db_mysql()
    cursor = db.cursor()
    sql = "SELECT member_num FROM wechat_group_action_copy1 "
    cursor.execute(sql.encode('utf-8'))
    data=cursor.fetchall()
    return data

def Updata_time(list,type):
    db = db_mysql()
    cursor = db.cursor()
    for member_num in list:
        sql = "UPDATE wechat_group_action_copy1 SET {2}='{0}' WHERE member_num='{1}'".format(datetime.datetime.now(),member_num,type)
        cursor.execute(sql)
    db.commit()
    db.close()

def Updata_member(member_num,member_name,display_name):
    db = db_mysql()
    cursor = db.cursor()
    sql = "UPDATE wechat_group_action_copy1 SET member_name='{0}' ,display_name='{2}' WHERE member_num='{1}'".format(member_name,
                                                                                   member_num, display_name)
    cursor.execute(sql)
    db.commit()
    db.close()



def getroom_message():
    list=[]
    name='test'
    '''获取群的username，对群成员进行分析需要用到'''
    itchat.update_chatroom(FromUserName)
    RoomList =  itchat.search_chatrooms(name=name)
    print(RoomList)
    if RoomList is None:
            print("%s group is not found!" % (name))
    else:
        User_list = RoomList[0]['MemberList']
        for User in User_list:
            UserName = User['UserName']
            NickName = User['NickName']
            display_name=User['DisplayName']
            Updata_member(UserName, NickName, display_name)
            if display_name:
                Updata_invite_member(UserName,display_name)
            else:
                Updata_invite_member(UserName, NickName)
            dic={ 'member_num':UserName,'member_name':NickName,'group_num':FromUserName,'group_name':name ,'display_name':display_name}
            IntoMysql_action(dic)
            list.append(UserName)
        return list

def Updata_invite_member(member_num,member_name):
    db = db_mysql()
    cursor = db.cursor()
    sql = "UPDATE wechat_group_invite_copy1 SET Inviter_num='{0}' WHERE Inviter='{1}'".format(member_num,
                                                                                        member_name)
    cursor.execute(sql)
    sql = "UPDATE wechat_group_invite_copy1 SET Invitee_num='{0}' WHERE Invitee='{1}'".format(member_num,
                                                                                        member_name)
    cursor.execute(sql)
    db.commit()
    db.close()


def add_remove():
    before=[]
    data_list=SelectMysql()
    for data in data_list:
        before.append(data[0])
    while True:
        time.sleep(10)
        after = getroom_message()
        add= [f for f in after if not f in before]
        removed = [f for f in before if not f in after]
        if removed:
            print("Removed: ", ", ".join(removed))
            Updata_time(removed, 'exit_time')
        if add:
            print("add: ", ", ".join(add))
            Updata_time(add, 'join_time')
        before=after




if __name__ == '__main__':
    itchat.auto_login(hotReload=True)
    try:
        threads = []
        t1 = threading.Thread(target=itchat.run(blockThread=False))
        threads.append(t1)
        t2 = threading.Thread(target=add_remove())
        threads.append(t2)
        for t in threads:
            t.setDaemon(False)
            t.start()
        for t in threads:
            t.join()
    except:
        traceback.print_exc()
        print("Error: unable to start thread")
