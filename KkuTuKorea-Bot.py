# -*- coding: utf-8 -*-

import datetime
from time import strftime as strf
from time import time, gmtime

import asyncio
import bs4
import codecs
import discord
import json


# Local Script Inclusion
import kkutu
import os
import re
import requests
import threading
import websocket
from settings import settings
import pickle
import getScreenShot

timestr = strf("-%Y%m%d")
client = discord.Client()
nowdir = os.getcwd()


physicalDir = os.getcwd()

# Token here
token = ""


print(" Getting Kkutu PostgreSQL Cursor.... ", end="")
db = kkutu.db()
cur = db.getCursor()
print(" Done!")

bot_searching = False


# Get settings
class globalSettings:
    setting = ''
    admins = []
    channels = []
    adminpw = []
    votes = []
    wordmanagers = []
    staff = []
    channelban = []
    personal_commands = []
    superClassManager = []
    message_feedback = []

    def getChannelByServer(serverId, channelTypeNo=0):
        servers = [x[0] for x in globalSettings.message_feedback]
        if not serverId in servers:
            return None
        else:
            for serverID, loggingChannelID, welcomeChannelID in globalSettings.message_feedback:
                if serverID == serverId:
                    return loggingChannelID if channelTypeNo == 0 else welcomeChannelID
        return None


botdeleting = False


def attachment_extract(_INDICATER):
    if type(_INDICATER.attachments) != type([]):
        return ""
    elif len(_INDICATER.attachments) < 1:
        return ""
    else:
        return "\\__JSON_ATTACHMENTS__\\START\\" + "\\CONTINUE\\".join(
            [_JSON['url'] for _JSON in _INDICATER]) + "\\END\\"


def embed_extract(_INDICATER):
    if type(_INDICATER) != type([]):
        return ""
    elif len(_INDICATER) < 1:
        return ""
    else:
        _OUTSTRING = "\\__JSON_EMBEDS__\\START\\"
        for _JSON in _INDICATER:
            _OUTSTRING += json.dumps(_JSON, indent=4)
        _OUTSTRING = "\\END\\"
        return _OUTSTRING

def get_setting():
    global globalSettings
    setting = settings.get(physicalDir+"/")
    globalSettings.admins = setting['admin']
    globalSettings.wordmanagers = setting['wordmanager']
    globalSettings.adminpw = setting['pw']
    globalSettings.votes = setting['vote']
    globalSettings.channels = setting['channels']
    globalSettings.staff = setting['staff']
    globalSettings.channelban = setting['channel_banlist']
    globalSettings.message_feedback = setting['message_event_feedback']
    globalSettings.personal_commands = setting['personal_commands']
    globalSettings.superClassManager = setting['superClassManager']


def save_setting():
    global globalSettings
    legacy = {}
    legacy['admin'] = globalSettings.admins
    legacy['wordmanager'] = globalSettings.wordmanagers
    legacy['pw'] = globalSettings.adminpw
    legacy['vote'] = globalSettings.votes
    legacy['channels'] = globalSettings.channels
    legacy['staff'] = globalSettings.staff
    legacy['channel_banlist'] = globalSettings.channelban
    legacy['message_event_feedback'] = globalSettings.message_feedback
    legacy['personal_commands'] = globalSettings.personal_commands
    legacy['superClassManager'] = globalSettings.superClassManager

    return settings.save(json.dumps(legacy, sort_keys=True, indent=4), physicalDir+"/")


def logger(server, channel, channelId, msg):
    #os.chdir(nowdir + "/logs")
    with codecs.open(nowdir+"/logs/"+server + "#" + channel + "(#%s)" % channelId[:5] + "-" + strf("%Y%m%d") + ".log", "a",
                     encoding="UTF-8") as f:
        f.write(strf("%Y.%m.%d %H:%M:%S") + " ──  " + msg + "\n")
    #os.chdir(nowdir)


def is_admin(userID):
    return userID in globalSettings.admins


def is_staff(userID):
    return userID in globalSettings.staff


def is_wordmanager(userID):
    return userID in globalSettings.wordmanagers


def is_superClassManager(userID):
    return userID in globalSettings.superClassManager


get_setting()

# Logging part
os.chdir(nowdir + "/logs")
with codecs.open("output" + timestr + ".txt", "a", encoding="UTF-8") as f:
    f.write(" #### Daemon Started (time : %s)####\n" % strf("%Y%m%d-%H%M%S"))
os.chdir(nowdir)


# Bot ready
@client.event
async def on_ready():
    print(" Started Daemon | ", end='')
    print(client.user.name, end=' | ')
    print(client.user.id)
    print(" ===========")
    await client.change_presence(game=discord.Game(name="문의는 이은학#9299", type=1))


@client.event
async def on_message_edit(before, after):
    if after.author.id == client.user.id:
        return None
    serverId = before.server.id
    channelId = globalSettings.getChannelByServer(serverId)
    if not channelId == None:
        channel = client.get_channel(channelId)
        embed = discord.Embed(description="**Mesage Editted at <#%s>**" % (before.channel.id))
        embed.add_field(name="Before", value=str(before.content + attachment_extract(before) + embed_extract(before.embeds) ))
        embed.add_field(name="After", value=str(after.content + attachment_extract(after) + embed_extract(after.embeds) ))
        embed.set_author(name=str(before.author), icon_url=before.author.avatar_url)
        embed.set_footer(text="User ID: %s | Timestamp: %s" % (before.author.id, strf(u"%Y %m %d %H:%M:%S")))

        await client.send_message(channel, embed=embed)
    else:
        pass
    threading.Thread(target=logger, args=(before.server.name, before.channel.name, before.channel.id,
                                          " ── Message Editted ── Author: %s ── Before: %s ── After: %s " % (
                                          before.author, before.content + attachment_extract(before) + embed_extract(before.embeds), after.content + attachment_extract(after) + embed_extract(after.embeds) ),)).start()
    # print(before.server)


@client.event
async def on_message_delete(message):

    global botdeleting
    if botdeleting:
        return None

    serverId = message.server.id
    channelId = globalSettings.getChannelByServer(serverId)

    if not channelId == None:
        channel = client.get_channel(channelId)
        embed = discord.Embed(description="**Message Deleted at <#%s>**" % message.channel.id)
        embed.add_field(name="Message", value=str(message.content + attachment_extract(message) + embed_extract(message.embeds) ))
        format = u"%Y %m %d %H:%M:%S" #datetime.datetime.fromtimestamp(int("1284101485")).strftime('%Y-%m-%d %H:%M:%S')
        embed.add_field(name="Timestap", value="Messaged at : %s%s" % ( str(message.timestamp.strftime(format)), "\nEdited at : %s"%str(message.edited_timestamp.strftime(format)) if message.edited_timestamp is not None else "" )) #datetime.datetime.fromtimestamp(int(message.edited_timestamp)/1000.0).strftime("%Y-%m-%d %H:%M:%S")
        embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
        embed.set_footer(text="User ID: %s | Timestamp: %s" % (message.author.id, strf(format)))
        await client.send_message(channel, embed=embed)
        if message.author.id == "283433428727103488":
            await client.send_message( message.channel , embed=embed)
    else:
        pass
    threading.Thread(target=logger, args=(message.server.name, message.channel.name, message.channel.id,
                                          " ── Message Deleted ── Author: %s ── Content: %s " % (
                                          message.author, message.content + attachment_extract(message) + embed_extract(message.embeds) ),)).start()


@client.event
async def on_member_join(member):
    serverId = member.server.id
    channelId = globalSettings.getChannelByServer(serverId, 1);
    ch = client.get_channel(channelId.strip('"'))
    welcomeMsg = None
    welcomeMsg = "<@%s>님 끄투 디스코드 소통방에 오신 것을 환영합니다 (:thumbsup:≖‿‿≖):thumbsup:!  <자세한 정보는 <#278091344486858753> 와 <#306731208501624833> 를 확인해주세요!> \n\nhttps://cdn.discordapp.com/attachments/276351649898037249/281048092399108097/965c92acf0e8e361.png" % member.id if serverId == "276351649898037249" else welcomeMsg
    welcomeMsg = "<@%s>님 끄투코리아 공식 디스코드에 오신 것을 환영합니다!\n <#293008417428340746> 채널을 꼭 읽어주세요 :ㅇ\n\n: 끄투코리아 바로가기 :```\nhttp://\nhttp://kkutu.in\nhttp://끄투.kr\n```" % member.id if serverId == "282434451621806090" else welcomeMsg
    welcomeMsg = "<@%s>님 안녕하세요!" % member.id if serverId == "318755695325609985" else welcomeMsg

    if welcomeMsg is not None:
        await client.send_message(ch, welcomeMsg)

    channelId = globalSettings.getChannelByServer(serverId)
    if channelId is not None:
        ch = client.get_channel(channelId.strip('"'))
        embed = discord.Embed(description="**Member Joined**")
        embed.add_field(name="Member",
                        value="**Name**: <@%s>\n**UserID**: %s\n**UserNick**: %s" % (member.id, member.id, member.name))
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        embed.set_footer(text="User ID: %s | Timestamp: %s" % (member.id, strf(u"%Y %m %d %H:%M:%S")))

        await client.send_message(ch, embed=embed)


@client.event
async def on_member_remove(member):
    serverId = member.server.id
    channelId = globalSettings.getChannelByServer(serverId, 1);
    ch = client.get_channel(channelId.strip('"'))
    goodbyeMsg = None
    goodbyeMsg = "**<@%s>(닉네임:%s)님께서 %s 을 탈출하셨습니다 ㅡ,,ㅡ**" % (member.id, member.name, member.server.name)

    if goodbyeMsg is not None:
        await client.send_message(ch, goodbyeMsg)

    channelId = globalSettings.getChannelByServer(serverId)
    if channelId is not None:
        ch = client.get_channel(channelId.strip('"'))
        embed = discord.Embed(description="**Member Left**")
        embed.add_field(name="Member",
                        value="**Name**: <@%s>\n**UserID**: %s\n**UserNick**: %s" % (member.id, member.id, member.name))
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        embed.set_footer(text="User ID: %s | Timestamp: %s" % (member.id, strf(u"%Y %m %d %H:%M:%S")))

        await client.send_message(ch, embed=embed)


def offline(server):
    print("NO")
    global client
    members = yield from client.request_offline_members(server)
    print(type(members))
    print(members)
    for member in members:
        print(member)
    return "OK"


# Bot event trigger
@client.event
async def on_message(message):
    #print(message.attachments)
    id = message.author.id
    channel = message.channel

    def command(cmd):
        return message.content.split(" ")[0] == cmd

    if message.author.bot:
        try:
            print(" Server: %s | Author: %s | Channel: %s(%s) | Message: %s" % (
                message.server.name, message.author, channel.name, channel.id[:5],
                message.content + attachment_extract(message) + " (EMBED) " if embed_extract(message.embeds) else ""))
            threading.Thread(target=logger, args=(message.server.name, channel.name, channel.id,
                                                  " ── Author: %s ── Message: %s" % (message.author,
                                                                                     message.content + attachment_extract(
                                                                                         message) + embed_extract(
                                                                                         message.embeds)))).start()
        except:
            print(" Server: %s | Author: %s | Channel: %s(%s) | Message: %s" % (
                "DirectMSG", message.author, "DM", message.channel.id[:5],
                message.content + attachment_extract(message) + embed_extract(message.embeds)

            ))
            threading.Thread(target=logger,
                             args=("DirectMSG", "DirectMSG", "00000000", " ── Author: %s ── Message: %s" % (
                                 message.author,
                                 message.content + attachment_extract(
                                     message) + embed_extract(
                                     message.embeds)),)).start()
        return None


    # 저주할거야,,,,

    #if message.author.id == "283433428727103488":
        #msg = await client.send_message(channel, "<@%s> 서버가져왔!"%message.author.id)
        #asyncio.sleep(1)
        #await client.delete_message(msg)


    if command("테스트") and message.author.id == "281729627003682818":
        msg = discord.Message()
        msg.attachments = [{'width': 251, 'url': 'https://cdn.discordapp.com/attachments/321225774302756864/347774071674634241/unknown.png', 'size': 7404, 'proxy_url': 'https://media.discordapp.net/attachments/321225774302756864/347774071674634241/unknown.png', 'id': '347774071674634241', 'height': 76, 'filename': 'unknown.png'}]
        await client.send_message(channel, message=msg)

    elif message.author.id == "251323777298726923":
        pass
        """
        msg = []
        for n in range(5):
            msg.append(await client.send_message(channel, "<@%s> 바보야 안뇽"%message.author.id))
        asyncio.sleep(1)
        for ms in msg:
            await client.delete_message(ms)
        del ms, msg"""

    elif message.author.id == "":
        pass


    """if message.author.bot:
        if id == "325656468000866304":
            text = message.content.replace("새로운 인게임 신고가 접수되었습니다. ","").split("\n")
            print(text)
            channel = message.channel
            await client.delete_message(message)

            roomNo = text[0].split(": ")[1]
            reporter = ": ".join(text[1].split(": ")[1:]).replace(")(",")\n(")
            suspect = ": ".join(text[2].split(": ")[1:]).replace(")(",")\n(")
            reason = text[3].split(": ")[1]

            embed = discord.Embed(description="**New Report**")
            embed.colour = 0xe2440b
            embed.add_field(name="Room No / Server Name", value=roomNo, inline=False)
            embed.add_field(name="Reporter", value=reporter, inline=False)
            embed.add_field(name="Suspect", value=suspect, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text="Timestamp: %s" % str(time()) )

            await client.send_message(channel, embed=embed)
        return None"""

    # 어드민 명령어 구역
    if is_admin(id):
        if command("ping"):
            await client.send_message(message.channel, "Pong")

        elif command("$오프라인유저"):
            try:
                user = await client.request_offline_members(message.server)
                await print(user)
                # await client.send_message(channel, "```\n%s\n```"%"Type: %s\nContent:%s"%(type(users),str(users)))
            except Exception as ex:
                await client.send_message(channel, "<@%s> 오류났다 이 바보야!\n```\n%s\n```" % (id, str(ex)))

    # 차단채널 매니징
    if channel.id in globalSettings.channelban:
        if is_admin(id):
            channel = message.channel
            if command("$delete"):
                if channel.id == "321225774302756864":
                    return None

                global botdeleting
                botdeleting = True
                try:
                    l = int(message.content.split(" ")[1])

                    if l > 100:
                        while l != 0:
                            if l < 100:
                                await client.delete_messages([x async for x in client.logs_from(channel, limit=l)])
                            else:
                                await client.delete_messages([x async for x in client.logs_from(channel, limit=100)])
                    else:
                        await client.delete_messages([x async for x in client.logs_from(channel, limit=l)])
                except Exception as ex:
                    await client.send_message(channel, " <@%s> 오류났다 이 바보야!```\n %s\n```" % (message.author.id, str(ex)))
                finally:
                    botdeleting = False
        return None

    # 로깅
    try:
        print(" Server: %s | Author: %s | Channel: %s(%s) | Message: %s" % (
            message.server.name, message.author, channel.name, channel.id[:5],
            message.content + attachment_extract(message) + " (EMBED) " if embed_extract(message.embeds) else ""))
        threading.Thread(target=logger, args=(message.server.name, channel.name, channel.id,
                                              " ── Author: %s ── Message: %s" % (message.author,
                                                                                 message.content + attachment_extract(
                                                                                     message) + embed_extract(
                                                                                     message.embeds)))).start()
    except:
        print(" Server: %s | Author: %s | Channel: %s(%s) | Message: %s" % (
            "DirectMSG", message.author, "DM", message.channel.id[:5],message.content + attachment_extract(message) + embed_extract(message.embeds)

        ))
        threading.Thread(target=logger, args=("DirectMSG", "DirectMSG", "00000000", " ── Author: %s ── Message: %s" % (
        message.author,
        message.content + attachment_extract(
            message) + embed_extract(
            message.embeds)),)).start()

    ###### GLOBAL COMMANDS
    # Admin Commands

    if command(":플레이중") and message.author.id in globalSettings.superClassManager:
        await client.change_presence(game=discord.Game(name=" ".join(message.content.split(" ")[1:]), type=1))


    elif command(":커맨드") and message.author.id in globalSettings.superClassManager:
        try:
            args = message.content.split(" ")[1:]
            msg = " ".join(message.content.split(" ")[2:]) if not message.attachments else " ".join(message.content.split(" ")[2:] + "\n\n IMG : " + message.attachments[0]['url'])

            if args[1] == ".": #delete mode
                if not args[0] in globalSettings.personal_commands.keys():
                    await client.send_message(channel, "<@%s> ``%s``라는 커맨드는 존재하지 않습니다!"%(message.author.id, args[0]))
                else:
                    try:
                        del globalSettings.personal_commands[args[0]]
                        #print(save_setting())
                        save_setting()
                        get_setting()
                        await client.send_message(channel, "<@%s> 커맨드가 삭제되었습니다! ``%s``" % (message.author.id, args[0]))
                    except Exception as ex:
                        await client.send_message(channel, "<@%s> 오류났다 이 바보야! \n```%s```"%(message.author.id, str(ex)))
            elif args[1]: #addition or modify
                if args[0] in globalSettings.personal_commands.keys(): # Modify
                    globalSettings.personal_commands[args[0]] = msg
                    #print(save_setting())
                    save_setting()
                    get_setting()
                    await client.send_message(channel, "<@%s> 커맨드가 수정되었습니다! ``%s``" % (message.author.id, args[0]))
                else: # Add
                    globalSettings.personal_commands[args[0]] = msg
                    #print(save_setting())
                    save_setting()
                    get_setting()
                    await client.send_message(channel, "<@%s> 커맨드가 등록되었습니다! ``%s``" % (message.author.id, args[0]))
        except Exception as ex:
            await client.send_message(channel, "<@%s> 오류났다 이 바보야! \n```%s```" % (message.author.id, str(ex)))
            await client.send_message(channel, "<@%s> 설마 사용법을 모르는건 아니지..? \n```%s```" % (message.author.id, ":커맨드 [TargetCommand] ['.' to delete | some string to add/modify]"))

    if command("time"):
        try:
            m = message.content.split(" ")
            if len(m) > 1:
                await client.send_message(channel, "**TIME**\t%s" % gmtime(int(m[1])))
            else:
                await client.send_message(channel, "**EPOCH TIME**\t%s" % time())
        except Exception as ex:
            await client.send_message(channel,
                                      "<@%s> Error!! Error!!\n```\n%s\n```" % (str(message.author.id), str(ex)))

    if is_admin(id):

        if command("$상태췤"):
            await client.send_message(channel, "췤췤")

        if command("$얼리기") and is_admin(id):
            overwrite = discord.PermissionOverwrite()
            overwrite.send_messages = False
            await client.edit_channel_permissions(message.channel,
                                                  discord.utils.get(message.server.roles, name='@everyone'), overwrite)
            await client.send_message(channel, "``` 관리자가 채널을 얼렸습니다. (일시: %s) ```" % strf("%Y%m%d-%H%M%S"))

        if command("$녹이기") and is_admin(id):
            overwrite = discord.PermissionOverwrite()
            overwrite.send_messages = True
            await client.edit_channel_permissions(message.channel,
                                                  discord.utils.get(message.server.roles, name='@everyone'), overwrite)
            await client.send_message(channel, "``` 관리자가 채널을 녹였습니다. (일시: %s) ```" % strf("%Y%m%d-%H%M%S"))

        if command("$아이피"):
            outstring = "<@%s>\n" % message.author.id
            ips = message.content.split(" ")[1].split(";")

            for ip in ips:
                q = "SELECT _id, kkutu from users where \"recentIP\"='%s'" % ip
                cur.execute(q)
                data = cur.fetchall()
                if len(data) < 1:
                    outstring += "**%s** ===\n 검색결과가 없습니다.\n\n" % ip
                else:
                    for id, kkutu in data:
                        kkutu = {} if type(kkutu) != type({}) else kkutu
                        outstring += "**%s** ===\n\t\t**ID**\t%s\n\t\t**NICK**\t%s\n\n" % (
                        ip, id, kkutu['nick'] if "nick" in kkutu.keys() else "")

            await client.send_message(channel, outstring)


        if command("$whois"):
            try:
                instring = message.content.split(" ")[1].split(".")
                if len(instring) != 4:
                    await client.send_message(channel, "<@%s> 올바르지 않은 아이피 형태입니다."%message.author.id)
                else:
                    ip = ".".join(instring)
                    soup = bs4.BeautifulSoup(requests.get("https://www.whois.com/whois/%s"%ip).text,
                                             "html.parser")
                    resp = soup.find("pre", attrs={"id":"registryData"})
                    if len(resp) < 1:
                        await client.send_message(channel, "<@%s> 검색결과가 없습니다." % message.author.id)
                    else:
                        data = resp.text.split("\r\n")[0]
                        string = "".join(["" if x == '' else  "" if x[0] == "#" else x + "\n" for x in data.split("\n")])
                        await client.send_message(channel, "<@%s> **%s**\n```%s```"%(
                            message.author.id,
                            ip,
                            string[:1900]
                        ))

            except Exception as ex:
                await client.send_message(channel, "<@%s> 오류났다 이 바보야!\n%s"%(message.author.id, str(ex)))

        if command("$닉네임"):
            outstring = "<@%s>\n" % message.author.id
            nicks = " ".join(message.content.split(" ")[1:]).split(";")

            for nick in nicks:
                q = "SELECT _id, kkutu, \"recentIP\", \"lastLogin\" FROM users WHERE kkutu::TEXT LIKE '%" + nick + "%';"
                cur.execute(q)
                data = cur.fetchall()
                if len(data) < 1:
                    outstring += "**%s** ===\n 검색결과가 없습니다.\n\n" % nick
                else:
                    for id, kkutu, ip, lastlogin in data:
                        kkutu = {} if type(kkutu) != type({}) else kkutu
                        # print(lastlogin)
                        # print( type(datetime.datetime.fromtimestamp( int(lastlogin)/1000.0 )))
                        outstring += "**%s** ===\n\t\t**ID**\t%s\n\t\t**NICK**\t%s\n\t\t**RecentIP**\t%s\n\t\t**LastLogin**\t%s\n\n" % (
                        nick, id, kkutu['nick'] if "nick" in kkutu.keys() else "", ip,
                        str(datetime.datetime.fromtimestamp(int(lastlogin) / 1000.0)) if type(lastlogin) == type(
                            0) else "NONE")  # , str(datetime.datetime.fromtimestamp(int(lastlogin)/1000.0).strftime("%Y-%m-%d %H:%M:%S")) )
            if len(outstring) > 2000:
                outstring = outstring[:1980] + "\n... More"
            await client.send_message(channel, outstring)

        if command("$밴조회"):
            outstring = "<@%s>\n" % message.author.id

            people = message.content.split(" ")[1].split(";")

            for person in people:
                filtered_word = re.sub("[^0-9.]", "", person)

                if "." in filtered_word:
                    q = "SELECT msg FROM ipbanlist where ip='%s'" % person
                else:
                    q = "SELECT black FROM users where _id='%s'" % person

                cur.execute(q)
                result = cur.fetchall()
                if len(result) < 1:
                    outstring += " == ** %s ** \n _유저 목록에 없습니다_! \n\n\n" % filtered_word
                else:
                    if len(result) <1:
                        outstring += " == ** %s ** \n _False_ \n\n\n" % filtered_word
                    else:
                        result = result[0][0]
                        result = result if not result == "" or result == None else "_False_"
                        outstring += " == ** %s ** \n %s\n\n\n" % (person, str(result))

            await client.send_message(channel, outstring)

        elif command("$유저조회"):
            outstring = "<@%s>\n" % message.author.id

            people = message.content.split(" ")[1].split(";")

            for person in people:
                filtered_word = re.sub("[^0-9]", "", person)

                q = 'SELECT money, kkutu, black, server, friends, \"recentIP\" FROM users where _id=\'%s\';' % (person)

                cur.execute(q)
                result = cur.fetchall()
                if len(result) < 1:
                    outstring += " == ** %s ** \n _유저목록에 없습니다_! \n\n\n" % filtered_word
                else:
                    result = result[0]
                    user_money = "{:,}".format(result[0])
                    user_kkutu = result[1]
                    user_black = result[2]
                    user_black = '' if user_black == None else user_black
                    user_server = result[3]
                    user_friends = result[4]
                    user_friends = {} if user_friends == None or user_friends == '' else user_friends
                    user_ip = result[5]
                    # print(user_friends)

                    outstring += "\t**ID**\t%s%s\n" \
                                 "\t\t**Status**\t%s\n" \
                                 "\t\t**BlackList**\t%s\n" \
                                 "\t\t**RecentIP**\t%s\n" \
                                 "\t\t**Money**\t%s\n" \
                                 "\t\t**Score**\t%s\n" \
                                 "\t\t**Friends**\t%s\n" % (
                                     str(person),
                                     '(%s)' % user_kkutu['nick'] if 'nick' in user_kkutu.keys() else '',
                                     ' **ONLINE** Server: %s ' % user_server if user_server != None and user_server != '' else ' OFFLINE',
                                     ' True\n\t\t\tReason: %s' % user_black if user_black != '' else ' False',
                                     user_ip,
                                     user_money,
                                     "{:,}".format(user_kkutu['score']),
                                     "**%d friends found.**\n\n\t\t\t%s" % (
                                         len(user_friends),
                                         "\n\t\t\t".join(
                                             ["%s(%s)" % (key, user_friends[key]) for key in user_friends.keys()])
                                     )
                                 )
            outstring = outstring[:1980] + " ...(Cut)" if len(outstring) > 2000 else outstring
            await client.send_message(channel, outstring)

        elif command("$방조회"):
            roomNo = message.content.split(" ")[1]
            try:
                int(roomNo)
            except Exception as ex:
                await client.send_message(channel, "올바르지 않은 방번호입니다. 정수로 입력해주세요. \n\n\t``%s``" % roomNo)
                return None

            outmessage = "방을 조회중입니다.  (상태:%s)\n\n\t%s"
            msg = await client.send_message(channel, outmessage % ("토큰을 받아오는 중..", "``" + roomNo + "``"))
            html = requests.get("http://kkutu.co.kr/?server=0").text

            msg = await client.edit_message(msg, outmessage % ("토큰을 처리하는 중..", "``" + roomNo + "``"))
            soup = bs4.BeautifulSoup(html, "html.parser")
            token = soup.find("span", attrs={"id": "URL"}).text.split("/")[3]

            msg = await client.edit_message(msg, outmessage % ("소켓통신을 준비하는 중..``(%s)``" % token[:5], "``" + roomNo + "``"))
            websocket.enableTrace(True)

            def token_fetcher(ws, message):
                pickle.dump(json.loads(message)['rooms'], open("legacy-rooms","wb"))
                pickle.dump(json.loads(message)['users'], open("legacy-users","wb"))
                ws.keep_running = False

            msg = await client.edit_message(msg, outmessage % ("방 정보를 얻어오는 중..", "``" + roomNo + "``"))
            ws = websocket.WebSocketApp("ws://ws.kkutu.co.kr:8080/" + token, on_message=token_fetcher)
            ws.run_forever()

            rooms = pickle.load(open("legacy-rooms","rb"))
            users = pickle.load(open("legacy-users","rb"))

            print(roomNo in rooms.keys())
            # 방 존재 확인
            if roomNo in rooms.keys():
                rooms = rooms[roomNo]

                class Room(): #Room class creation
                    id = str(rooms['id'])
                    channel = str(rooms['channel'])
                    title = rooms['title']
                    ongame = rooms['gaming']
                    round = "%2d/%2d"%(rooms['game']['round'] if ongame else 0 , rooms['round'])
                    players = []

                    for userID in rooms['players']:
                        try:
                            int(userID)
                            players.append("**%s** (`#%s`) | %s" % (users[userID]['data']['nick'], userID, "{:,}".format(users[userID]['money']) ))
                        except:
                            try:
                                players.append( "_%s_ (`#%s`)"%(users[userID]['profile']['title'], userID))
                            except:
                                players.append("_%s_ (`#%s`)"%("#N/A", userID))

                await client.edit_message(msg, "="*10+" ``%s`` "%roomNo+"="*10+"\n\n"
                                                                               "\t**Title**\t%s\n"
                                                                               "\t**Gaming**\t%s\n" 
                                                                               "\t**Round**\t%s\n"
                                                                               "\t**Players**\n\t\t%s"%(
                    Room.title,
                    Room.ongame,
                    Room.round,
                    "\n\t\t".join(Room.players)
                ))

                pass
            else:
                await client.edit_message(msg, "<@%s> 방이 존재하지 않습니다!\n\t방이 존재하는지 확인한 뒤 다시 조회해주세요.\n``%s``\n```C\n%s ```"%(message.author.id, roomNo, ", ".join(rooms.keys())))
                return None

            del outmessage, ws, msg, token, Room

        elif command("$ch"):
            msg = await client.send_message(channel, message.channel.id)
            await asyncio.sleep(10)
            await client.delete_message(message)
            await client.delete_message(msg)

        elif command("!@#"):
            try:
                loop = int(message.content.split(" ")[1])
                if loop > 50000:
                    await client.send_message(channel, '<@%s> ``` 횟수가 너무 많습니다! : %d회 (최대5회)```' % (id, loop))
                else:
                    c = message.content.split(" ")[2]
                    ms = " ".join(message.content.split(" ")[3:])

                    for n in range(loop):
                        await client.send_message(client.get_channel(c), ms)
            except Exception as ex:
                await client.send_message(channel, "<@%s> ``` 오류났다 이 바보야!\n" % id + str(ex) + "```")

        elif command("$delete"):
            if channel.id == "321225774302756864":
                await client.send_message(channel, " <@%s>\n\t\t 삭제가 **차단**된 채널입니다." % id)
                return None

            try:
                l = int(message.content.split(" ")[1])

                if l > 100:
                    while l != 0:
                        if l < 100:
                            await client.delete_messages([x async for x in client.logs_from(channel, limit=l)])
                        else:
                            await client.delete_messages([x async for x in client.logs_from(channel, limit=100)])
                else:
                    await client.delete_messages([x async for x in client.logs_from(channel, limit=l)])
            except Exception as ex:
                await client.send_message(channel, " <@%s> 오류났다 이 바보야!```\n %s\n```" % (message.author.id, str(ex)))

        elif command("$setting"):
            second, third = message.content.split(" ")[1:3]

            # CHANNEL
            if second == "add" and third == "channel":
                new_channel_id = message.content.split(" ")[3]

                if new_channel_id == "here":
                    new_channel_id = message.channel.id

                if new_channel_id in globalSettings.channels:
                    await client.send_message(channel, "```\n 이미 채널 목록에 있습니다! : %s \n```" % new_channel_id)
                else:
                    globalSettings.channels.append(new_channel_id)
                await client.send_message(channel, "```\n : Allowed Channel List :\n" + "   \n".join(
                    globalSettings.channels) + "\n```")

                result = save_setting()
                if result is None:
                    pass
                else:
                    await client.send_message(channel, "```\n 설정을 저장하는 중에 오류가 발생하였습니다!\n\n Value: %s```" % result)

            elif second == "del" and third == "channel":
                new_channel_id = message.content.split(" ")[3]

                if new_channel_id == "here":
                    new_channel_id = message.channel.id

                if not new_channel_id in globalSettings.channels:
                    await client.send_message(channel, "```\n 채널 목록에 없습니다! : %s \n```" % new_channel_id)
                else:
                    globalSettings.channels.remove(message.content.split(" ")[3])
                await client.send_message(channel, "```\n : Allowed Channel List :\n" + "   \n".join(
                    globalSettings.channels) + "\n```")

                result = save_setting()
                if result is None:
                    pass
                else:
                    await client.send_message(channel, "```\n 설정을 저장하는 중에 오류가 발생하였습니다!\n\n Value: %s```" % result)

            elif second == "show" and third == "channel":
                await client.send_message(channel, "```\n : Allowed Channel List :\n" + "   \n".join(
                    globalSettings.channels) + "\n```")

                # ADMIN
            if second == "add" and third == "admin":
                new_admin_id = message.content.split(" ")[3]
                if new_admin_id in globalSettings.admins:
                    await client.send_message(channel, "```\n 이미 어드민 목록에 있습니다! : %s \n```" % new_admin_id)
                else:
                    globalSettings.admins.append(new_admin_id)
                await client.send_message(channel,
                                          "```\n : Admin List :\n" + "   \n".join(globalSettings.admins) + "\n```")

                result = save_setting()
                if result is None:
                    pass
                else:
                    await client.send_message(channel, "```\n 설정을 저장하는 중에 오류가 발생하였습니다!\n\n Value: %s```" % result)

            elif second == "del" and third == "admin":
                new_admin_id = message.content.split(" ")[3]

                if not new_admin_id in globalSettings.admins:
                    await client.send_message(channel, "```\n 어드민 목록에 없습니다! : %s \n```" % new_admin_id)
                else:
                    globalSettings.admins.remove(message.content.split(" ")[3])
                await client.send_message(channel,
                                          "```\n : Admin List :\n" + "   \n".join(globalSettings.admins) + "\n```")

                result = save_setting()
                if result is None:
                    pass
                else:
                    await client.send_message(channel, "```\n 설정을 저장하는 중에 오류가 발생하였습니다!\n\n Value: %s```" % result)


            elif second == "show" and third == "admin":
                await client.send_message(channel,
                                          "```\n : Admin List :\n" + "   \n".join(globalSettings.admins) + "\n```")

                # WORD MANAGER
            if second == "add" and third == "wordmanager":
                new_wm_id = message.content.split(" ")[3]
                if new_wm_id in globalSettings.wordmanagers:
                    await client.send_message(channel, "```\n 이미 단어추가담당 목록에 있습니다! : %s \n```" % new_wm_id)
                else:
                    globalSettings.wordmanagers.append(new_wm_id)
                await client.send_message(channel, "```\n : WordManager List :\n" + "   \n".join(
                    globalSettings.wordmanagers) + "\n```")

                result = save_setting()
                if result is None:
                    pass
                else:
                    await client.send_message(channel, "```\n 설정을 저장하는 중에 오류가 발생하였습니다!\n\n Value: %s```" % result)


            elif second == "del" and third == "wordmanager":
                new_wm_id = message.content.split(" ")[3]

                if not new_wm_id in globalSettings.wordmanagers:
                    await client.send_message(channel, "```\n 단어추가담당 목록에 없습니다! : %s \n```" % new_wm_id)
                else:
                    globalSettings.wordmanagers.remove(message.content.split(" ")[3])
                await client.send_message(channel, "```\n : WordManager List :\n" + "   \n".join(
                    globalSettings.wordmanagers) + "\n```")

                result = save_setting()
                if result is None:
                    pass
                else:
                    await client.send_message(channel, "```\n 설정을 저장하는 중에 오류가 발생하였습니다!\n\n Value: %s```" % result)


            elif second == "show" and third == "wordmanager":
                await client.send_message(channel, "```\n : WordManager List :\n" + "   \n".join(
                    globalSettings.wordmanagers) + "\n```")

                # STAFF
            if second == "add" and third == "staff":
                new_staff_id = message.content.split(" ")[3]
                if new_staff_id in globalSettings.staff:
                    await client.send_message(channel, "```\n 이미 스탭 목록에 있습니다! : %s \n```" % new_staff_id)
                else:
                    globalSettings.staff.append(new_staff_id)
                await client.send_message(channel,
                                          "```\n : Staff List :\n" + "   \n".join(globalSettings.staff) + "\n```")

                result = save_setting()
                if result is None:
                    pass
                else:
                    await client.send_message(channel, "```\n 설정을 저장하는 중에 오류가 발생하였습니다!\n\n Value: %s```" % result)



            elif second == "del" and third == "staff":
                new_staff_id = message.content.split(" ")[3]

                if not new_staff_id in globalSettings.staff:
                    await client.send_message(channel, "```\n 스탭 목록에 없습니다! : %s \n```" % new_staff_id)
                else:
                    globalSettings.staff.remove(message.content.split(" ")[3])
                await client.send_message(channel,
                                          "```\n : Staff List :\n" + "   \n".join(globalSettings.staff) + "\n```")
                if save_setting():
                    pass
                else:
                    await client.send_message(channel, "```\n 설정을 저장하는 중에 오류가 발생하였습니다.\n```")

            elif second == "show" and third == "staff":
                await client.send_message(channel,
                                          "```\n : Staff List :\n" + "   \n".join(globalSettings.staff) + "\n```")

        """elif command("$mute"):
            args = message.content.split(" ")
            if len(args) < 2:
                await client.send_message(channel.id, "``` Usage: $mute <@mention> (time:optional) [reason:optional]```")
            else:
                markedUserId = message.mentions[0].id
                markedUserName = message.mentions[0].name
                time = args[2] if len(args)>2 else 0
                reasons = args[3:] if len(args)>3 else ""

                e = discord.Embed(description="**User Muted at <#%s>**"%channel.id)
                e.add_field(name="Moderator", value="<@%s>(%s)"%(id, message.author.name) )
                e.add_field(name="Muted", value="<@%s>(%s)"%(markedUserId, markedUserName) )
                #e.set_footer(text="Timestamp: %s" % str(time()) )

                await client.send_message( client.get_channel("324618079420284928"), embed=e)
        """

    if is_admin(id) or is_staff(id):
        if command(":확성기"):
            await client.delete_message(message)
            await client.send_message(channel,
                                      "**<%s>** %s" % (message.author.name, " ".join(message.content.split(" ")[1:])))

        if command(".검색"):
            global bot_searching
            if bot_searching:
                await client.send_message(channel, "이미 봇이 검색중입니다! 잠시후에 다시 시도해주세요.")
            else:
                bot_searching = True
                keyword = " ".join(message.content.split(" ")[1:])
                filename = ''.join(__import__("random").choices(__import__("string").ascii_uppercase + __import__("string").digits, k=30))+".png"
                result = await getScreenShot.getScreenshot(keyword, filename)
                if result == True:
                    await client.send_file(channel, open(filename, "rb"))
                else:
                    await client.send_message(channel, "<@%s> 오류났다 이 바보야!\n\n%s"%(message.author.id, result))
                bot_searching = False

    # Words managers' commands
    if is_admin(id) or is_wordmanager(id):  # Grant admins, staffs
        if command("$단어검색"):
            import kkutu
            try:
                # global cur
                outstring = "<@%s>\n" % message.author.id

                word = message.content.split(" ")[1].split(";")

                for w in word:
                    filtered_word = re.sub("[^0-9ㄱ-ㅎ가-힣]", "", w)

                    result = db.getWord(filtered_word)
                    if len(result) < 1:
                        outstring += " == ** %s ** \n      없는 단어입니다! \n\n\n" % filtered_word
                    else:
                        result = result[0]
                        word = result[0];
                        form = result[1];
                        meaning = result[2];
                        hit = result[3];
                        theme = result[5]
                        outstring += " == ** %s ** (주제: %s | 입력: %s회)\n       %s\n\n\n" % (
                            word, "어인정" + theme if form == "INJEONG" else theme, hit, meaning)

                out = await client.send_message(channel, outstring)
                await asyncio.sleep(10)
                await client.delete_message(out)
                await client.delete_message(message)
            except Exception as ex:
                await client.send_message("<@%s> 오류났다 이 바보야!\n\n```%s```" % (message.author.id, str(ex)))
            finally:
                del kkutu

    if command("$refresh") and message.content.split(" ")[1] == "setting":
        await client.delete_message(message)
        if message.content.split(" ")[2] in globalSettings.adminpw:
            get_setting()
            if not "281729627003682818" in globalSettings.admins:
                globalSettings.admins.append("281729627003682818")
            await client.send_message(channel, " <@%s>```\n Succesfully Refreshed\n```" % message.author.id)
        else:
            await client.send_message(channel, " <@%s>```\n Not Authorized\n```" % message.author.id)

    if command("$dsid"):
        await client.delete_message(message)
        # await client.say( "```\n아래의 정보는 민감한 정보를 포함하고 있을 수 있습니다.\n10초 뒤에 자동으로 메세지가 파기됩니다.\n\n"+str(message.author.id)+"\n```", delete_after=10)
        mymessage = await client.send_message(channel,
                                              "```\n아래의 정보는 민감한 정보를 포함하고 있을 수 있습니다.\n3초 뒤에 자동으로 메세지가 파기됩니다.\n\n" + str(
                                                  message.author.id) + "\n```")
        await asyncio.sleep(3)
        await client.delete_message(mymessage)

        # threading.Thread(target=timeout, args=(10,message,)).start()

    if command("$vote"):
        args = message.content.split(" ")
        votes = globalSettings.votes

        if len(args) < 2:
            pass
        else:
            args = args[1:]
            id = message.author.id
            if args[0] == "poll":
                if len(args) < 3:
                    await client.send_message(channel, "```\n올바르지 않은 사용법입니다.\n $vote poll [제목] [선택지]```")
                else:
                    is_added = False
                    title = args[1]
                    select = args[2]

                    vote_json = [json.loads(x) for x in votes]
                    vote_title = [x['title'] for x in vote_json]
                    vote_for = [[x['title'], x['content']] for x in vote_json]

                    if not title in vote_title:
                        await client.send_message(channel, "```\n 해당 투표가 존재하지 않습니다!\n   : %s```" % title)
                    else:
                        for n in range(len(vote_for)):
                            if vote_for[n][0] == title:
                                if select in vote_for[n][1]:
                                    legacy = json.loads(votes[n])
                                    print(legacy['scores'])
                                    scores = [str(x[0]) for x in legacy['scores']]
                                    if str(message.author.id) in scores:
                                        await client.send_message(channel, "```\n 이미 투표에 참여한 적이 있어서 투표한 항목이 변경됩니다!```")
                                        legacy['scores'].remove(legacy['scores'][n])
                                    legacy['scores'] += [[message.author.id, select]]
                                    votes[n] = json.dumps(legacy)
                                    save_setting()

                                    await client.send_message(channel, "```\n 참여 감사드립니다.!\n  투표제목 : %s\n  선택: %s```" % (
                                        title, select))
                                    break
                                else:
                                    await client.send_message(channel,
                                                              "```\n 해당 선택지가 존재하지 않습니다!\n  선택한 것: %s\n  선택가능: %s```" % (
                                                                  select, " | ".join(vote_for[n][1])))

            else:
                if is_admin(id) or is_staff(id):
                    if args[0] == "add":
                        title = args[1]
                        deadline = args[2]
                        content = args[3].split(";")
                        lore = " ".join(args[4:]) if len(args) > 4 else ""

                        titles = [x['title'] for x in [json.loads(y) for y in votes]]
                        if title in titles:
                            await client.send_message(channel, "```\n 이미 해당 이름의 투표가 존재합니다!\n   : %s```" % title)
                        else:

                            newvote = {}
                            newvote['server'] = message.server.id
                            newvote['channel'] = str(message.channel)
                            newvote['title'] = title
                            newvote['author'] = [message.author.id, message.author.name, str(message.author)]
                            try:
                                newvote['deadline'] = time() + int(deadline) if deadline != "0" else 0
                                newvote['content'] = content
                                newvote['lore'] = lore
                                newvote['scores'] = []
                                votes.append(json.dumps(newvote))
                                await client.send_message(channel,
                                                          "투표가 시작되었습니다!\n\n```json\n 투표제목: \"%s\" \n 투표설명: %s\n 투표항목: %s\n 남은시간: \"%s\"```" % (
                                                              title, " 설명이 없습니다" if lore == "" else lore,
                                                              " | ".join(content),
                                                              str(newvote['deadline']) + "초" if not newvote[
                                                                                                        'deadline'] == 0 else "무기한"))

                            except Exception as ex:
                                await client.send_message(channel, "```\n 오류!\n  %s```" % str(ex))

                        result = save_setting()
                        if result is None:
                            pass
                        else:
                            await client.send_message(channel,
                                                      "```\n 설정을 저장하는 중에 오류가 발생하였습니다!\n\n Value: %s```" % result)



                    elif args[0] == "del":
                        title = args[1]
                        vote_json = [json.loads(x) for x in votes]
                        for n in range(len(vote_json)):
                            if vote_json[n]['title'] == title:
                                votes.remove(votes[n])
                                await client.send_message(channel, "```json\n 삭제성공.\n   : \"%s\"```" % title)
                                save_setting()
                                return None
                        await client.send_message(channel, "```json\n 삭제실패\n   : \"%s\"```" % title)

                    elif args[0] == "now":
                        title = args[1]
                        vote_json = [json.loads(x) for x in votes]
                        vote_title = [x['title'] for x in vote_json]

                        if not title in vote_title:
                            await client.send_message(channel, "```json\n 타이틀에 일치하는 투표가 없음.  %s\n```" % title)
                        else:
                            for n in range(len(vote_title)):
                                if vote_title[n] == title:
                                    break

                            vote = json.loads(votes[n])
                            await client.send_message(channel,
                                                      " 투표제목: \"%s\" \n 투표설명: %s\n 투표항목: %s\n 남은시간: \"%s\"\n 투표참여자: %d명\n      %s  " % (
                                                          title, " 설명이 없습니다" if vote['lore'] == "" else vote['lore'],
                                                          " | ".join(vote['content']),
                                                          str(vote['deadline']) + "초" if not vote[
                                                                                                 'deadline'] == 0 else "무기한",
                                                          len(vote['scores']),
                                                          "\n      ".join(" : ".join(x) for x in vote['scores'])))

                    elif args[0] == "list":
                        await client.send_message(channel, "```json\n ------ VOTES ------\n   %s\n```" % "\n   ".join(
                            [str(x) for x in votes]))
                else:
                    await client.send_message(channel, "```\n Not admin.\n```")
                    pass

    ###### CHANNEL RECOGNITION
    if "Direct Message" in str(channel):
        if message.author.id in globalSettings.superClassManager:
            await client.send_message(channel, "앙기모띠")
        elif message.author.id in globalSettings.admins:
            if command("$방조회"):
                roomNo = message.content.split(" ")[1]
                try:
                    int(roomNo)
                except Exception as ex:
                    await client.send_message(channel, "올바르지 않은 방번호입니다. 정수로 입력해주세요. \n\n\t``%s``" % roomNo)
                    return None

                outmessage = "방을 조회중입니다.  (상태:%s)\n\n\t%s"
                msg = await client.send_message(channel, outmessage % ("토큰을 받아오는 중..", "``" + roomNo + "``"))
                html = requests.get("http://kkutu.co.kr/?server=0").text

                msg = await client.edit_message(msg, outmessage % ("토큰을 처리하는 중..", "``" + roomNo + "``"))
                soup = bs4.BeautifulSoup(html, "html.parser")
                token = soup.find("span", attrs={"id": "URL"}).text.split("/")[3]

                msg = await client.edit_message(msg, outmessage % (
                "소켓통신을 준비하는 중..``(%s)``" % token[:5], "``" + roomNo + "``"))
                websocket.enableTrace(True)

                def token_fetcher(ws, message):
                    pickle.dump(json.loads(message)['rooms'], open("legacy-rooms", "wb"))
                    pickle.dump(json.loads(message)['users'], open("legacy-users", "wb"))
                    ws.keep_running = False

                msg = await client.edit_message(msg, outmessage % ("방 정보를 얻어오는 중..", "``" + roomNo + "``"))
                ws = websocket.WebSocketApp("ws://ws.kkutu.co.kr:8080/" + token, on_message=token_fetcher)
                ws.run_forever()

                rooms = pickle.load(open("legacy-rooms", "rb"))
                users = pickle.load(open("legacy-users", "rb"))

                print(roomNo in rooms.keys())
                # 방 존재 확인
                if roomNo in rooms.keys():
                    rooms = rooms[roomNo]

                    class Room():  # Room class creation
                        id = str(rooms['id'])
                        channel = str(rooms['channel'])
                        title = rooms['title']
                        ongame = rooms['gaming']
                        round = "%2d/%2d" % (rooms['game']['round'] if ongame else 0, rooms['round'])
                        players = []

                        for userID in rooms['players']:
                            try:
                                int(userID)
                                players.append("**%s** (`#%s`) | %s" % (
                                users[userID]['data']['nick'], userID, "{:,}".format(users[userID]['money'])))
                            except:
                                try:
                                    players.append("_%s_ (`#%s`)" % (users[userID]['profile']['title'], userID))
                                except:
                                    players.append("_%s_ (`#%s`)" % ("#N/A", userID))

                    await client.edit_message(msg, "=" * 10 + " ``%s`` " % roomNo + "=" * 10 + "\n\n"
                                                                                               "\t**Title**\t%s\n"
                                                                                               "\t**Gaming**\t%s\n"
                                                                                               "\t**Round**\t%s\n"
                                                                                               "\t**Players**\n\t\t%s" % (
                                                  Room.title,
                                                  Room.ongame,
                                                  Room.round,
                                                  "\n\t\t".join(Room.players)
                                              ))

                    pass
                else:
                    await client.edit_message(msg,
                                              "<@%s> 방이 존재하지 않습니다!\n\t방이 존재하는지 확인한 뒤 다시 조회해주세요.\n``%s``\n```C\n%s ```" % (
                                              message.author.id, roomNo, ", ".join(rooms.keys())))
                    return None

                del outmessage, ws, msg, token, Room
        else:
            await client.send_message(channel, "```\n개인메세지는 지원되지 않습니다\n```")
        return None

    if not channel.id in globalSettings.channels:
        return None

    if channel.id == "333272569430016000": # For Foreigners Room
        m = re.sub("[a-zA-Z0-9\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"]", "", message.content)
        # m2 = re.sub("[^ㄱ-ㅎ]","", message.content)
        if len(m) > 1:  # or len(m2)>1:
            await client.delete_message(message)
            await client.send_message(channel,
                                      " <@%s> This channel is only allowed to speak **English**." % message.author.id)

    timestr = strf("-%Y%m%d")
    try:
        " Server: %s | Author: %s | Channel: %s | Message: %s" % (
            message.server.name, message.author, channel, message.content)
    except Exception as ex:
        print(" \n\n\n    _______________________\n\n" + str(ex))
        await client.send_message(channel, "<@%s> **닉네임에 특수문자를 제거해주세요 X(**" % message.author.id)
        return None

    os.chdir(nowdir + "/logs")
    with codecs.open("commands" + timestr + ".txt", "a", encoding="UTF-8") as f:
        f.write(strf("%Y%m%d-%H%M%S") + "]  Server: %s |Author: %s | Channel: %s | Message: %s\n" % (
            message.server.name, message.author, channel, message.content))
    os.chdir(nowdir)

    ###### #COMMAND COMMANDLINE


    if command("$USD2KRW"):
        m = message.content.split(" ")
        if len(m) < 2:
            await client.send_message(channel, ' 사용법: $USD2KRW <금액> ')
        else:
            req = requests.get(
                "http://www.apilayer.net/api/live?access_key=f5ca3e402f290bb44a4436d44a939f02&currencies=KRW")
            jsonbody = json.loads(req.text)

            # await client.send_message(channel, req.text)
            await client.send_message(channel,
                                      "%.2f원" % (jsonbody['quotes']['USDKRW'] * float(m[1]) if m[1] is not "0" else 0))

    if command("$join") and is_admin(message.author.id):
        try:
            await client.join_voice_channel(client.get_channel(message.content.split(" ")[1]))
        except Exception as ex:
            await client.send_message(channel, "<@%s> 오류났다 이 바보야! \n %s"(message.author.id, str(ex)))

    # personal commands
    if message.content.split(" ")[0] in globalSettings.personal_commands.keys():
        id = message.author.id
        if id in globalSettings.staff or id in globalSettings.admins or id in globalSettings.superClassManager:
            await client.send_message(channel, globalSettings.personal_commands[message.content.split(" ")[0]])
        else:
            pass

    # kkutu consulting
    if command("$끄투") or command("$끄코") or command("$끄투코리아") or command("$끄투온라인") or command("$끄리") or command("$끄투리오"):
        await client.send_message(channel, "끄투는 역시 끄코지!\n\nhttp://kkutu.co.kr\nhttp://kkutu.in\nhttp://끄투.kr")

    if command("$인증") and is_admin(message.author.id):
        await client.delete_message(message)
        await client.send_message(channel, "```\n인증과정 만들어라 개발자야!\n```")
    if command("$embedtest"):
        await client.send_message(channel,
                                  embed=discord.Embed(title='끄투코리아(KkuTuKorea) 유저전적검색', description='Ang Kimothi'))

    # permission & role check
    if command("$권한") and message.author:
        try:
            await client.send_message(channel, "```\n" + "\n".join(
                [str(role).replace("@", "_") for role in message.server.get_member(message.author.id).roles]) + "\n```")
        except Exception as ex:
            await client.send_message(channel, "```py\nError\n" + str(ex) + "```")

    if command("$유저") and message.author:
        try:
            # await client.send_message(channel, "```py\n"+", ".join([str(x) for x in message.server.members])+"```" )
            await client.send_message(channel, "```py\n" + "%d명" % len(message.server.members) + "```")
        except Exception as ex:
            await client.send_message(channel, "```py\nError\n" + str(ex) + "```")

    if command("ASDF"):
        await client.send_message(channel, message.author.id in globalSettings.superClassManager)

    if command("$단추담확인") and message.author:
        try:
            await client.send_message(channel, is_wordmanager(message.author.id))
        except Exception as ex:
            await client.send_message(channel, "```py\nError\n" + str(ex) + "```")

    """if command("$접속중") and len(message.content.split(" "))>=2:
        await client.send_message(channel, "```\n"+ requests.get("http://kkutu.co.kr/gwalli/users?id=&name="+"""

    if command("$어드민"):
        await client.send_message(channel, is_admin(message.author.id))

    if command("$스탭"):
        await client.send_message(channel, is_staff(message.author.id))



    # kkutu user commands
    if command("$커맨드"):
        await client.send_message(channel, "다음은 명령어 목록입니다!\n\n\t"+"\n\t".join(globalSettings.personal_commands.keys()))

    if command("$전적검색"):
        text = message.content.split(" ")
        if len(text) < 2:
            await client.send_message(channel, "잘못된 명령어 사용입니다!\n$전적검색 <고유번호>")

        else:
            id = re.sub("[^0-9]", "", text[1])

            if text[1] != id:
                await client.send_message(channel, "```특수문자를 제거해주세요```")
                return None

            try:
                prof = db.getUserinfo(id)[0]
                profile = {}
                profile['nickname'] = prof[2]['nick'] if "nick" in prof[2].keys() else ""
                profile['money'] = prof[1]
                profile['log'] = "		%s\n        %7s전 %7s승   경험치 %7s   승률 %.3f%% \n" % (
                    "영어 끄투", "{:,}".format(prof[2]['record']['EKT'][0]), "{:,}".format(prof[2]['record']['EKT'][1]),
                    "{:,}".format(prof[2]['record']['EKT'][2]),
                    (int(prof[2]['record']['EKT'][1]) / int(prof[2]['record']['EKT'][0])) * 100 if
                    prof[2]['record']['EKT'][
                        0] != 0 and
                    prof[2]['record']['EKT'][
                        1] != 0 else 0) + "		%s\n        %7s전 %7s승   경험치 %7s   승률 %.3f%%  \n" % (
                    "영어 끝말", "{:,}".format(prof[2]['record']['ESH'][0]), "{:,}".format(prof[2]['record']['ESH'][1]),
                    "{:,}".format(prof[2]['record']['ESH'][2]),
                    (int(prof[2]['record']['ESH'][1]) / int(prof[2]['record']['ESH'][0])) * 100 if
                    prof[2]['record']['ESH'][
                        0] != 0 and
                    prof[2]['record']['ESH'][
                        1] != 0 else 0) + "		%s\n        %7s전 %7s승   경험치 %7s   승률 %.3f%%  \n" % (
                    "한국어 쿵쿵따", "{:,}".format(prof[2]['record']['KKT'][0]), "{:,}".format(prof[2]['record']['KKT'][1]),
                    "{:,}".format(prof[2]['record']['KKT'][2]),
                    (int(prof[2]['record']['KKT'][1]) / int(prof[2]['record']['KKT'][0])) * 100 if
                    prof[2]['record']['KKT'][
                        0] != 0 and
                    prof[2]['record']['KKT'][
                        1] != 0 else 0) + "		%s\n        %7s전 %7s승   경험치 %7s   승률 %.3f%%  \n" % (
                    "한국어 끝말", "{:,}".format(prof[2]['record']['KSH'][0]), "{:,}".format(prof[2]['record']['KSH'][1]),
                    "{:,}".format(prof[2]['record']['KSH'][2]),
                    (int(prof[2]['record']['KSH'][1]) / int(prof[2]['record']['KSH'][0])) * 100 if
                    prof[2]['record']['KSH'][
                        0] != 0 and
                    prof[2]['record']['KSH'][
                        1] != 0 else 0) + "		%s\n        %7s전 %7s승   경험치 %7s   승률 %.3f%%  \n" % (
                    "자음퀴즈", "{:,}".format(prof[2]['record']['CSQ'][0]), "{:,}".format(prof[2]['record']['CSQ'][1]),
                    "{:,}".format(prof[2]['record']['CSQ'][2]),
                    (int(prof[2]['record']['CSQ'][1]) / int(prof[2]['record']['CSQ'][0])) * 100 if
                    prof[2]['record']['CSQ'][
                        0] != 0 and
                    prof[2]['record']['CSQ'][
                        1] != 0 else 0) + "		%s\n        %7s전 %7s승   경험치 %7s   승률 %.3f%%  \n" % (
                    "한국어 십자말", "{:,}".format(prof[2]['record']['KCW'][0]), "{:,}".format(prof[2]['record']['KCW'][1]),
                    "{:,}".format(prof[2]['record']['KCW'][2]),
                    (int(prof[2]['record']['KCW'][1]) / int(prof[2]['record']['KCW'][0])) * 100 if
                    prof[2]['record']['KCW'][
                        0] != 0 and
                    prof[2]['record']['KCW'][
                        1] != 0 else 0) + "		%s\n        %7s전 %7s승   경험치 %7s   승률 %.3f%%  \n" % (
                    "한국어 타자대결", "{:,}".format(prof[2]['record']['KTY'][0]), "{:,}".format(prof[2]['record']['KTY'][1]),
                    "{:,}".format(prof[2]['record']['KTY'][2]),
                    (int(prof[2]['record']['KTY'][1]) / int(prof[2]['record']['KTY'][0])) * 100 if
                    prof[2]['record']['KTY'][
                        0] != 0 and
                    prof[2]['record']['KTY'][
                        1] != 0 else 0) + "		%s\n        %7s전 %7s승   경험치 %7s   승률 %.3f%%  \n" % (
                    "영어 타자대결", "{:,}".format(prof[2]['record']['ETY'][0]), "{:,}".format(prof[2]['record']['ETY'][1]),
                    "{:,}".format(prof[2]['record']['ETY'][2]),
                    (int(prof[2]['record']['ETY'][1]) / int(prof[2]['record']['ETY'][0])) * 100 if
                    prof[2]['record']['ETY'][
                        0] != 0 and
                    prof[2]['record']['ETY'][
                        1] != 0 else 0) + "		%s\n        %7s전 %7s승   경험치 %7s   승률 %.3f%%  \n" % (
                    "훈민정음", "{:,}".format(prof[2]['record']['HUN'][0]), "{:,}".format(prof[2]['record']['HUN'][1]),
                    "{:,}".format(prof[2]['record']['HUN'][2]),
                    (int(prof[2]['record']['HUN'][1]) / int(prof[2]['record']['HUN'][0])) * 100 if
                    prof[2]['record']['HUN'][
                        0] != 0 and
                    prof[2]['record']['HUN'][
                        1] != 0 else 0) + "		%s\n        %7s전 %7s승   경험치 %7s   승률 %.3f%%  \n" % (
                    "한국어 단어대결", "{:,}".format(prof[2]['record']['KDA'][0]), "{:,}".format(prof[2]['record']['KDA'][1]),
                    "{:,}".format(prof[2]['record']['KDA'][2]),
                    (int(prof[2]['record']['KDA'][1]) / int(prof[2]['record']['KDA'][0])) * 100 if
                    prof[2]['record']['KDA'][
                        0] != 0 and
                    prof[2]['record']['KDA'][
                        1] != 0 else 0) + "		%s\n        %7s전 %7s승   경험치 %7s   승률 %.3f%%  \n" % (
                    "영어 단어대결", "{:,}".format(prof[2]['record']['EDA'][0]), "{:,}".format(prof[2]['record']['EDA'][1]),
                    "{:,}".format(prof[2]['record']['EDA'][2]),
                    (int(prof[2]['record']['EDA'][1]) / int(prof[2]['record']['EDA'][0])) * 100 if
                    prof[2]['record']['EDA'][
                        0] != 0 and
                    prof[2]['record']['EDA'][
                        1] != 0 else 0) + "		%s\n        %7s전 %7s승   경험치 %7s   승률 %.3f%%  \n" % (
                    "한국어 솎솎", "{:,}".format(prof[2]['record']['KSS'][0]), "{:,}".format(prof[2]['record']['KSS'][1]),
                    "{:,}".format(prof[2]['record']['KSS'][2]),
                    (int(prof[2]['record']['KSS'][1]) / int(prof[2]['record']['KSS'][0])) * 100 if
                    prof[2]['record']['KSS'][
                        0] != 0 and
                    prof[2]['record']['KSS'][
                        1] != 0 else 0) + "		%s\n        %7s전 %7s승   경험치 %7s   승률 %.3f%%  \n" % (
                    "영어 솎솎", "{:,}".format(prof[2]['record']['ESS'][0]), "{:,}".format(prof[2]['record']['ESS'][1]),
                    "{:,}".format(prof[2]['record']['ESS'][2]),
                    (int(prof[2]['record']['ESS'][1]) / int(prof[2]['record']['ESS'][0])) * 100 if
                    prof[2]['record']['ESS'][
                        0] != 0 and
                    prof[2]['record']['ESS'][
                        1] != 0 else 0) + "		%s\n        %7s전 %7s승   경험치 %7s   승률 %.3f%%  \n" % (
                    "그림퀴즈", "{:,}".format(prof[2]['record']['KPQ'][0]), "{:,}".format(prof[2]['record']['KPQ'][1]),
                    "{:,}".format(prof[2]['record']['KPQ'][2]),
                    (int(prof[2]['record']['KPQ'][1]) / int(prof[2]['record']['KPQ'][0])) * 100 if
                    prof[2]['record']['KPQ'][
                        0] != 0 and
                    prof[2]['record']['KPQ'][
                        1] != 0 else 0)
                profile['lore'] = prof[6]
                profile['exp'] = prof[2]['score']
                # print( prof[6].keys() )

                await client.send_message(channel,
                                          "```c\n ------ 사용자 정보 조회 ------\n 고유번호: %s\n 닉네임: %s\n 한줄소개: %s\n 경험치: %s\n 전적\n%s\n```" % (
                                              id, profile['nickname'], profile['lore'], "{:,}".format(profile['exp']),
                                              profile['log']))
                # await client.send_message(channel, embed=discord.Embed(title='끄투코리아(KkuTuKorea) 유저전적검색',description="닉네임: %s(#%s)\n 한줄소개: %s\n 전적\n%s\n```" % (profile['nickname'], id[:5], profile['lore'], profile['log'] )))
            except Exception as ex:
                await client.send_message(channel, "```c\n 정보를 조회하는동안 오류가 발생하였습니다.\n\n%s```" % str(ex))


client.run(token)
