# script/PokePal/main.py

import logging
import os
import random
import sys
import re
import asyncio

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import owner_id
from app.api import *
from app.switch import load_switch, save_switch

# 数据存储路径，实际开发时，请将PokePal替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "PokePal",
)

# 表情列表
emoji_list = [
    4,
    5,
    8,
    9,
    10,
    12,
    14,
    16,
    21,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    32,
    33,
    34,
    38,
    39,
    41,
    42,
    43,
    49,
    53,
    60,
    63,
    66,
    74,
    75,
    76,
    78,
    79,
    85,
    89,
    96,
    97,
    98,
    99,
    100,
    101,
    102,
    103,
    104,
    106,
    109,
    111,
    116,
    118,
    120,
    122,
    123,
    124,
    125,
    129,
    144,
    147,
    171,
    173,
    174,
    175,
    176,
    179,
    180,
    181,
    182,
    183,
    201,
    203,
    212,
    214,
    219,
    222,
    227,
    232,
    240,
    243,
    246,
    262,
    264,
    265,
    266,
    267,
    268,
    269,
    270,
    271,
    272,
    273,
    277,
    278,
    281,
    282,
    284,
    285,
    287,
    289,
    290,
    293,
    294,
    297,
    298,
    299,
    305,
    306,
    307,
    314,
    315,
    318,
    319,
    320,
    322,
    324,
    326,
    9728,
    9749,
    9786,
    10024,
    10060,
    10068,
    127801,
    127817,
    127822,
    127827,
    127836,
    127838,
    127847,
    127866,
    127867,
    127881,
    128027,
    128046,
    128051,
    128053,
    128074,
    128076,
    128077,
    128079,
    128089,
    128102,
    128104,
    128147,
    128157,
    128164,
    128166,
    128168,
    128170,
    128235,
    128293,
    128513,
    128514,
    128516,
    128522,
    128524,
    128527,
    128530,
    128531,
    128532,
    128536,
    128538,
    128540,
    128541,
    128557,
    128560,
    128563,
]


# 查看功能开关状态
def load_function_status(group_id):
    return load_switch(group_id, "PokePal")


# 保存功能开关状态
def save_function_status(group_id, status):
    save_switch(group_id, "PokePal", status)


# 对已知消息id的消息戳1个表情戳指定次数
async def poke_a_message_by_id(websocket, message_id, count):
    emoji_id = random.choice(emoji_list)
    for _ in range(count):
        await set_msg_emoji_like(websocket, message_id, emoji_id, set=True)
        await asyncio.sleep(0.1)
        await set_msg_emoji_like(websocket, message_id, emoji_id, set=False)


# 对已知消息id的消息戳20个表情
async def poke_a_message_by_id_20(websocket, message_id):
    for _ in range(20):
        emoji_id = random.choice(emoji_list)
        await set_msg_emoji_like(websocket, message_id, emoji_id)


# 群消息处理函数
async def handle_PokePal_group_message(websocket, msg):
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        role = str(msg.get("sender", {}).get("role"))
        message_id = str(msg.get("message_id"))

        # 鉴权
        # if user_id not in owner_id:
        #     return

        if raw_message.startswith("[CQ:reply,id="):
            match = re.search(r"\[CQ:reply,id=(\d+)\].*骚扰", raw_message)
            match_with_count = re.search(
                r"\[CQ:reply,id=(\d+)\].*骚扰(\d+)", raw_message
            )
            if match_with_count:
                reply_id = match_with_count.group(1)
                count = match_with_count.group(2)
                # 对单条消息进行骚扰
                await poke_a_message_by_id(websocket, reply_id, int(count))
            elif match:
                reply_id = match.group(1)
                # 对单条消息进行骚扰
                await poke_a_message_by_id_20(websocket, reply_id)

    except Exception as e:
        logging.error(f"处理PokePal群消息失败: {e}")
        return


# 统一事件处理入口
async def handle_events(websocket, msg):
    """统一事件处理入口"""
    try:
        # 处理回调事件
        if msg.get("status") == "ok":
            return

        post_type = msg.get("post_type")

        # 处理元事件
        if post_type == "meta_event":
            return

        # 处理消息事件
        elif post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                # 调用PokePal的群组消息处理函数
                await handle_PokePal_group_message(websocket, msg)
            elif message_type == "private":
                return

        # 处理通知事件
        elif post_type == "notice":
            return

        # 处理请求事件
        elif post_type == "request":
            return

    except Exception as e:
        error_type = {
            "message": "消息",
            "notice": "通知",
            "request": "请求",
            "meta_event": "元事件",
        }.get(post_type, "未知")

        logging.error(f"处理PokePal{error_type}事件失败: {e}")

        # 发送错误提示
        if post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                await send_group_msg(
                    websocket,
                    msg.get("group_id"),
                    f"处理PokePal{error_type}事件失败，错误信息：{str(e)}",
                )
            elif message_type == "private":
                await send_private_msg(
                    websocket,
                    msg.get("user_id"),
                    f"处理PokePal{error_type}事件失败，错误信息：{str(e)}",
                )
