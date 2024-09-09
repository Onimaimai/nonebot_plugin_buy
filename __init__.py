import json
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.typing import T_State
from nonebot.adapters import Message
from nonebot.params import CommandArg


__zx_plugin_name__ = "团购 help"


# File to store group-buying data
data_file = "./data/groupbuy_data.json"
activity_file = "./data/activity_data.json"

# Load group-buying data
def load_data():
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save group-buying data
def save_data(data):
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

        
# Help command to show plugin information
groupbuy_help = on_command("团购 help", aliases={"groupbuyhelp"}, priority=5)

@groupbuy_help.handle()
async def handle_groupbuy_help(bot: Bot, event: Event):
    help_message = (
        "开团 <名称> <成团金额>\n"
        "拼团 <名称> <参与金额>\n"
        "重置团购 <名称>\n"
        "删除团购 <名称>\n"
        "查询团购 <名称>\n"
        "团购列表\n"
        "添加活动 <名称>\n"
        "参加活动 <名称>\n"
        "重置活动 <名称>\n"
        "删除活动 <名称>\n"
        "查询活动 <名称>\n"
        "活动列表"
    )
    await groupbuy_help.finish(help_message)
        
        
# Add a new group-buying project
add_groupbuy = on_command("开团", aliases={"add_groupbuy"}, priority=5)

@add_groupbuy.handle()
async def handle_add_groupbuy(bot: Bot, event: Event, state: T_State, args: Message = CommandArg()):
    args_list = args.extract_plain_text().split()
    if len(args_list) != 2:
        await add_groupbuy.finish("请输入正确的格式：开团 <名称> <成团金额>")
        return
    
    group_id = str(event.group_id)
    project_name = args_list[0]
    target_amount = float(args_list[1])

    data = load_data()

    if group_id not in data:
        data[group_id] = {}

    if project_name in data[group_id]:
        await add_groupbuy.finish(f"团购项目 '{project_name}' 已存在！")
        return

    data[group_id][project_name] = {
        "target_amount": target_amount,
        "participants": {},
        "total_amount": 0
    }

    save_data(data)
    await add_groupbuy.finish(f"'{project_name}' 开团成功，成团金额为 {target_amount}！")

# Participate in a group-buying project
participate_groupbuy = on_command("拼团", aliases={"participate_groupbuy"}, priority=5)

@participate_groupbuy.handle()
async def handle_participate_groupbuy(bot: Bot, event: Event, state: T_State, args: Message = CommandArg()):
    args_list = args.extract_plain_text().split()
    if len(args_list) != 2:
        await participate_groupbuy.finish("请输入正确的格式：拼团 <名称> <参与金额>")
        return
    
    group_id = str(event.group_id)
    user_id = str(event.user_id)
    nickname = event.sender.card if event.sender.card else event.sender.nickname
    project_name = args_list[0]
    amount = float(args_list[1])

    data = load_data()

    if group_id not in data or project_name not in data[group_id]:
        await participate_groupbuy.finish(f"未找到团购项目 '{project_name}'！")
        return

    project = data[group_id][project_name]

    if amount == 0:
        # Remove the participant's record
        if user_id in project['participants']:
            project['total_amount'] -= project['participants'][user_id]['amount']
            del project['participants'][user_id]
            save_data(data)
            await participate_groupbuy.finish(f"{nickname} 已从团购 '{project_name}' 中移除！")
        else:
            await participate_groupbuy.finish(f"{nickname} 未参与团购 '{project_name}'！")
    else:
        # Add or update the participant's record
        if user_id in project['participants']:
            project['total_amount'] -= project['participants'][user_id]['amount']

        project['participants'][user_id] = {
            "nickname": nickname,
            "user_id": user_id,
            "amount": amount
        }
        project['total_amount'] += amount

        # Check if the total amount exceeds the target amount
        if project['total_amount'] == project['target_amount']:
            participant_list = "\n".join(
                [f"{p['nickname']}：{p['amount']}元" for p in project['participants'].values()])
            await participate_groupbuy.send(f"团购 '{project_name}' 已成团！参与成员：\n{participant_list}")
        elif project['total_amount'] > project['target_amount']:
            project['total_amount'] -= amount
            del project['participants'][user_id]
            await participate_groupbuy.send(f"参与金额超出成团金额，{nickname} 的参与金额被移除！")
        else:
            await participate_groupbuy.send(f"{nickname} 参与了团购 '{project_name}'，当前金额为 {project['total_amount']} 元。")

        save_data(data)

# Reset a group-buying project
reset_groupbuy = on_command("重置团购", aliases={"reset_groupbuy"}, priority=5)

@reset_groupbuy.handle()
async def handle_reset_groupbuy(bot: Bot, event: Event, state: T_State, args: Message = CommandArg()):
    project_name = args.extract_plain_text().strip()

    if not project_name:
        await reset_groupbuy.finish("请输入团购名称：重置团购 <名称>")
        return
    
    group_id = str(event.group_id)
    data = load_data()

    if group_id not in data or project_name not in data[group_id]:
        await reset_groupbuy.finish(f"未找到团购项目 '{project_name}'！")
        return

    # Reset the project to initial state
    target_amount = data[group_id][project_name]['target_amount']
    data[group_id][project_name] = {
        "target_amount": target_amount,
        "participants": {},
        "total_amount": 0
    }

    save_data(data)
    await reset_groupbuy.finish(f"团购 '{project_name}' 已重置！")

# Delete a group-buying project
delete_groupbuy = on_command("删除团购", aliases={"delete_groupbuy"}, priority=5)

@delete_groupbuy.handle()
async def handle_delete_groupbuy(bot: Bot, event: Event, state: T_State, args: Message = CommandArg()):
    project_name = args.extract_plain_text().strip()

    if not project_name:
        await delete_groupbuy.finish("请输入团购名称：删除团购 <名称>")
        return
    
    group_id = str(event.group_id)
    data = load_data()

    if group_id not in data or project_name not in data[group_id]:
        await delete_groupbuy.finish(f"未找到团购 '{project_name}'！")
        return

    # Remove the project
    del data[group_id][project_name]

    if not data[group_id]:  # If no projects left in the group, remove the group entry
        del data[group_id]

    save_data(data)
    await delete_groupbuy.finish(f"团购 '{project_name}' 已删除！")

# List all group-buying projects in the group
list_groupbuy = on_command("团购列表", aliases={"list_groupbuy"}, priority=5)

@list_groupbuy.handle()
async def handle_list_groupbuy(bot: Bot, event: Event):
    group_id = str(event.group_id)
    data = load_data()

    if group_id not in data or not data[group_id]:
        await list_groupbuy.finish("本群尚未添加任何团购。")
        return

    project_list = "\n".join(f"- {name} (成团金额: {info['target_amount']} 元)" for name, info in data[group_id].items())
    await list_groupbuy.finish(f"本群的团购列表：\n{project_list}")

# Query details of a specific group-buying project
query_groupbuy = on_command("查询团购", aliases={"query_groupbuy"}, priority=5)

@query_groupbuy.handle()
async def handle_query_groupbuy(bot: Bot, event: Event, state: T_State, args: Message = CommandArg()):
    project_name = args.extract_plain_text().strip()

    if not project_name:
        await query_groupbuy.finish("请输入团购名称：查询团购 <名称>")
        return
    
    group_id = str(event.group_id)
    data = load_data()

    if group_id not in data or project_name not in data[group_id]:
        await query_groupbuy.finish(f"未找到团购 '{project_name}'！")
        return

    project = data[group_id][project_name]
    participant_list = "\n".join(
        [f"{p['nickname']}\n({p['user_id']})：{p['amount']}元" for p in project['participants'].values()]
    )
    remaining_amount = project['target_amount'] - project['total_amount']
    
    response = (
        f"团购 '{project_name}' ：\n"
        f"成团金额：{project['target_amount']} 元\n"
        f"当前金额：{project['total_amount']} 元\n"
        f"剩余金额：{remaining_amount} 元\n"
        f"参与成员：\n{participant_list if participant_list else '暂无参与成员'}"
    )

    await query_groupbuy.finish(response)

    
    
    
    
add_activity = on_command("添加活动", aliases={"add_activity"}, priority=5)

@add_activity.handle()
async def handle_add_activity(bot: Bot, event: Event, state: T_State, args: Message = CommandArg()):
    args_list = args.extract_plain_text().split()
    if len(args_list) != 1:
        await add_activity.finish("请输入正确的格式：添加活动 <名称>")
        return
    
    group_id = str(event.group_id)
    activity_name = args_list[0]

    data = load_data()

    if group_id not in data:
        data[group_id] = {}

    if activity_name in data[group_id]:
        await add_activity.finish(f"活动 '{activity_name}' 已存在！")
        return

    data[group_id][activity_name] = {
        "participants": [],
    }

    save_data(data)
    await add_activity.finish(f"活动 '{activity_name}' 添加成功！")

    
participate_activity = on_command("参加活动", aliases={"participate_activity"}, priority=5)

@participate_activity.handle()
async def handle_participate_activity(bot: Bot, event: Event, state: T_State, args: Message = CommandArg()):
    activity_name = args.extract_plain_text().strip()

    if not activity_name:
        await participate_activity.finish("请输入正确的格式：参加活动 <名称>")
        return
    
    group_id = str(event.group_id)
    user_id = str(event.user_id)
    nickname = event.sender.card if event.sender.card else event.sender.nickname

    data = load_data()

    if group_id not in data or activity_name not in data[group_id]:
        await participate_activity.finish(f"未找到活动 '{activity_name}'！")
        return

    activity = data[group_id][activity_name]

    if user_id not in activity['participants']:
        activity['participants'].append({"nickname": nickname, "user_id": user_id})

    save_data(data)
    await participate_activity.finish(f"{nickname} 已参加活动 '{activity_name}'！")

    
reset_activity = on_command("重置活动", aliases={"reset_activity"}, priority=5)

@reset_activity.handle()
async def handle_reset_activity(bot: Bot, event: Event, state: T_State, args: Message = CommandArg()):
    activity_name = args.extract_plain_text().strip()

    if not activity_name:
        await reset_activity.finish("请输入活动名称：重置活动 <名称>")
        return
    
    group_id = str(event.group_id)
    data = load_data()

    if group_id not in data or activity_name not in data[group_id]:
        await reset_activity.finish(f"未找到活动 '{activity_name}'！")
        return

    # 重置活动
    data[group_id][activity_name]['participants'] = []

    save_data(data)
    await reset_activity.finish(f"活动 '{activity_name}' 已重置！")

    
delete_activity = on_command("删除活动", aliases={"delete_activity"}, priority=5)

@delete_activity.handle()
async def handle_delete_activity(bot: Bot, event: Event, state: T_State, args: Message = CommandArg()):
    activity_name = args.extract_plain_text().strip()

    if not activity_name:
        await delete_activity.finish("请输入活动名称：删除活动 <名称>")
        return
    
    group_id = str(event.group_id)
    data = load_data()

    if group_id not in data or activity_name not in data[group_id]:
        await delete_activity.finish(f"未找到活动 '{activity_name}'！")
        return

    # 删除活动
    del data[group_id][activity_name]

    if not data[group_id]:
        del data[group_id]

    save_data(data)
    await delete_activity.finish(f"活动 '{activity_name}' 已删除！")

    
query_activity = on_command("查询活动", aliases={"query_activity"}, priority=5)

@query_activity.handle()
async def handle_query_activity(bot: Bot, event: Event, state: T_State, args: Message = CommandArg()):
    activity_name = args.extract_plain_text().strip()

    if not activity_name:
        await query_activity.finish("请输入活动名称：查询活动 <名称>")
        return
    
    group_id = str(event.group_id)
    data = load_data()

    if group_id not in data or activity_name not in data[group_id]:
        await query_activity.finish(f"未找到活动 '{activity_name}'！")
        return

    activity = data[group_id][activity_name]
    participant_list = "\n".join(
        [f"{p['nickname']}\n({p['user_id']})" for p in activity['participants']]
    )

    response = f"活动 '{activity_name}' ：\n参与成员：\n{participant_list if participant_list else '暂无参与成员'}"
    await query_activity.finish(response)

    
list_activity = on_command("活动列表", aliases={"list_activity"}, priority=5)

@list_activity.handle()
async def handle_list_activity(bot: Bot, event: Event):
    group_id = str(event.group_id)
    data = load_data()

    if group_id not in data or not data[group_id]:
        await list_activity.finish("本群尚未添加任何活动。")
        return

    activity_list = "\n".join(f"- {name}" for name in data[group_id].keys())
    await list_activity.finish(f"本群的活动列表：\n{activity_list}")
