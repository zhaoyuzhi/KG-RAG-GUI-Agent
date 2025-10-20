def get_action_prompt(instruction, history):

# -------------------------------------------------------任务描述-------------------------------------------------------

    prompt = f"""你是一个擅长操作智能手机的AI助手。这张图片是手机当前界面的截图。请根据用户指令“{instruction}”，确定接下来需要执行的单步交互操作。每个单步交互操作可以对一个可交互控件进行一次操作，或者调用一次系统级操作。\n"""
    # prompt += "当你确定的操作涉及某个控件时，你需要详细描述控件的功能、外观和位置，以便用户能够准确理解你的操作。\n"


# -------------------------------------------------------交互操作-------------------------------------------------------

#     prompt += """\n### 交互操作
#  可用的单步交互操作包括以下四类：
# 1. click：点击一个控件。当使用此操作时，你需要详细描述选定的控件。
# 2. input：在一个可输入文本的控件中输入指定内容。当使用此操作时，你需要详细描述选定的控件和输入的内容。
# 3. swipe：滑动一个控件。当使用此操作时，你需要详细描述选定的控件和滑动的方向。滑动方向包括“向上”、“向下”、“向左”和“向右”。
# 4. back: 系统级操作‘返回’，回到当前界面之前的界面。
# 你只能从以上四类操作中选择一个，因此请只考虑紧接着的操作步骤。\n"""

    prompt += """\n### 交互操作
 可用的单步交互操作包括以下四类：
1. 点击：点击一个控件。当使用此操作时，你需要详细描述选定的控件。
2. 输入：在一个可输入文本的控件中输入指定内容。当使用此操作时，你需要详细描述选定的控件和输入的内容。
3. 滑动：滑动一个控件。当使用此操作时，你需要详细描述选定的控件和滑动的方向。滑动方向包括“向上”、“向下”、“向左”和“向右”。
4. 返回: 系统级操作‘返回’，回到当前界面之前的界面。
你只能从以上四类操作中选择一个，因此请只考虑紧接着的操作步骤。\n"""

# -------------------------------------------------------操作意图-------------------------------------------------------

    # prompt += f"\n### 操作意图\n当前的操作意图是：{instruction}\n"


# -------------------------------------------------------历史操作-------------------------------------------------------

#     if len(history) > 0:
#         prompt += """\n### 历史操作
# 为了实现操作意图，你曾经做出了一些操作，并预测了操作后的效果：\n"""
# #         prompt += """\n### 历史操作
# # 为了实现操作意图，你曾经做出了一些操作：\n"""
#         for i in range(len(history)):
#             prompt += f"{i + 1}. {history[i]}\n"
#         prompt += """记住，历史操作不一定是正确的，你应该批判性的看待它们。\n"""


# -------------------------------------------------------无效操作-------------------------------------------------------

#     prompt += """\n### 无效操作
# 你曾经在当前页面中做出过一些无效的操作，这些操作并没有使操作意图得以实现，你应该避免重复它们：
# 1. 点击了页面右上角的搜索按钮，以便搜索“雷军”并找到他的最新微博。
# 2. 点击页面左上角的搜索按钮进入搜索界面，以便能够搜索“雷军”找到他的最新微博。
# 记住，历史操作不一定是正确的，你应该批判性的看待它们。\n"""


# -------------------------------------------------------参考案例-------------------------------------------------------

#     prompt += """\n### 参考案例
# 在完成类似操作意图时，你曾经按照以下步骤达成了目标：
# 1. 点击右下角的“我的”图标，寻找登录选项。
# 2. 为了进入登录页面，点击“用户登录”按钮。
# 3. 在手机号输入框输入了“13701231234”。
# 4. 在密码输入框中输入密码“654321”。
# 5. 勾选同意用户协议的复选框。
# 6. 账号和密码已经输入，接下来点击“登录”按钮以完成登录操作。
# 该参考案例可能不是每个步骤都和你要实现的目标吻合，你应该自主选择有参考价值的步骤。\n"""

#     prompt += """\n### 参考案例
# 在完成类似操作意图时，你曾经按照以下步骤达成了目标：
# 1. 我点击了林俊杰的歌曲《江南》以进入该歌曲的页面。
# 2. 点击页面底部的正在播放《江南》的信息栏，以进入该歌曲的详细页面，从而进行评论。
# 3. 点击当前页面的评论按钮进入评论界面。
# 4. 我在页面底部的评论输入框中输入了“真好听”。
# 5. 点击发送按钮以发布“真好听”的评论。\n"""


# ---------------------------------------------------------提示---------------------------------------------------------

#     prompt += """\n### 提示
# 1. 你只能进行一次交互操作，即进行一次点击/输入/滑动/返回操作。因此，你只需要考虑紧接着的操作步骤。
# 2. 你需要判断当前页面与操作意图是否处在一个功能模组中，如果不是，可能需要先返回到主页面或上层页面。
# 3. 在查找内容时，搜索通常比滚动页面更有效。请只在你非常确定目标内容无法通过搜索找到时才使用滚动页面进行查找。
# 4. 你需要判断当前页面处于的具体条目或内容是否是操作意图指定的条目或内容，如果不是，你的操作应该是找到正确的条目或内容。
# 5. 确保你操作的条目或内容和操作意图完全对应非常重要。页面中有一些条目或内容可能和操作意图部分相关，但你不应该就这些条目或内容进行操作，而是应该寻找和操作意图完全对应的条目或内容。\n"""
#     if len(history) > 0:
#         prompt += "6. 如果你感觉历史操作没有实现预期的效果，不要考虑操作失败请考虑其他思路而不是重复同一操作。\n"

# -------------------------------------------------------输出格式-------------------------------------------------------

#     prompt += """\n### 输出格式
# 你的输出应包括以下三个部分，并按照给定格式：
# 1. 观察：<描述你在应用界面中观察到的内容，尤其是与用户指令相关的部分。>
# 2. 推理：<根据用户指令，用自然语言完整描述你推理出正确的单步交互操作的过程。>
# 3. 操作：<从“交互操作”中描述四类操作中选择一个执行。当选择“click”、“input”或“swipe”时，详细描述控件的功能、外观和位置。选择输入或滑动时，还需说明输入内容或滑动方向。>\n"""

    prompt += """\n### 输出格式
你的输出应包括以下三个部分，并按照给定格式：
1. 观察：<描述你在应用界面中观察到的内容，尤其是与用户指令相关的部分。>
2. 推理：<根据用户指令，用自然语言完整描述你推理出正确的单步交互操作的过程。>
3. 操作：<从“交互操作”中描述四类操作中选择一个执行。当选择“点击”、“输入”或“滑动”时，必须详细描述控件的功能、外观、绝对位置和相对位置。选择输入或滑动时，还需说明输入内容或滑动方向。>\n"""

#     prompt += """\n### 输出格式
# 你的输出应包括以下几个部分，并按照此格式：
# 1. 观察：<描述你在应用界面中观察到的内容，尤其是与用户指令相关的部分。>
# 2. 推理：<根据用户指令，用自然语言完整描述你推理出正确的单步交互操作的过程。>
# 3. 操作类型：<从“交互操作”中描述四类操作中选择一个。>
# 4. 控件描述：<如果你选择的交互操作是“click”、“input”或“swipe”，详细描述所涉及的控件的功能、外观、以及位置。如果选择是“返回”，填写“N/A”。>
# 5. 输入内容：<如果你选择的交互操作是“input”，说明要输入的内容；如果选择的不是“input”，填写“N/A”。>
# 6. 滑动方向：<如果你选择的交互操作是“swipe”，说明滑动的方向；如果选择的不是“swipe”，填写“N/A”。>"""

#     prompt += """\n### 输出格式
# 你的输出应包括以下几个部分，并按照此格式：
# 1. 观察：<描述你在应用界面中观察到的内容，尤其是与用户指令相关的部分。>
# 2. 推理：<根据用户指令，用自然语言完整描述你推理出正确的单步交互操作的过程。>
# 3. 操作类型：<从“交互操作”中描述四类操作中选择一个。>
# 4. 控件描述：<如果你选择的交互操作是“click”、“input”或“swipe”，说明所涉及的控件的类型，如“搜索框”、“暂停”、“播放”、“文本”等。如果控件无法归类，请描述控件的外观。如果选择是“back”，填写“N/A”。>
# 5. 控件上的文本：<如果你选择的交互操作是“click”、“input”或“swipe”，且所涉及的控件上包含文本，填写控件上的文本内容。如果选择是“back”或控件上不带文本，填写“N/A”。>
# 6. 控件绝对位置：<如果你选择的交互操作是“click”、“input”或“swipe”，说明所涉及的控件在页面中的绝对位置，包括“左上”、“上”、“右上”、“左”、“中”、“右”、“左下”、“下”、“右下”九种。如果选择是“back”，填写“N/A”。>
# 7. 控件相对位置：<如果你选择的交互操作是“click”、“input”或“swipe”，详细描述所涉及的控件在页面中的相对位置，即它相对于页面中其他元素的位置。如果选择是“back”，填写“N/A”。>
# 8. 输入内容：<如果你选择的交互操作是“input”，说明要输入的内容；如果选择的不是“input”，填写“N/A”。>
# 9. 滑动方向：<如果你选择的交互操作是“swipe”，说明滑动的方向；如果选择的不是“swipe”，填写“N/A”。>
# 注意，如果你选择的交互操作是“click”、“input”或“swipe”，且多个控件都能达成目标时，你必须指明其中一个。"""

# -------------------------------------------------------回答示例-------------------------------------------------------

#     prompt += """\n### 回答示例
# - 示例1（操作意图为“播放甄嬛传”）：
# 1. 观察： 当前界面是影视类应用的主界面。页面顶部有一个搜索栏（标签为2），其中预填的内容是“庆余年”。下方是各种影视类别的标签，当前选中的是“古装”。标签栏下方是若干古装影视作品的标题、海报和基本信息。页面底部是控制栏，有“主页”、“会员专区”、“发现”和“我的”四个选项。
# 2. 思考：为了播放《甄嬛传》，我需要在搜索栏中输入“甄嬛传”并搜索。最有效的下一个单步交互操作是在搜索栏（标签为2）中输入“甄嬛传”。
# 3. 操作：`text(2, "甄嬛传")`
#
# - 示例2（操作意图为“播放热门摇滚乐列表”）：
# 1. 观察：当前界面显示音乐类应用的主页。页面顶部是一个搜索栏，下方是用户当前的播放列表和“猜你爱听”的歌曲目录。再下方有各种热门音乐排行榜，其中包含“摇滚乐榜”（标签为4）。页面底部是控制栏，有“首页”、“直播”、“雷达”、“派对”、“我的”五个选项。
# 2. 思考：为了播放热门摇滚乐列表，最有效的下一个单步交互操作是点击热门音乐排行榜中的“摇滚乐榜”（标签为4）。
# 3. 操作：`click(4)`
#
# - 示例3（操作意图为“购买一双雪地靴”）：
# 1. 观察：当前界面处于购物类应用内置的游戏模块“芭芭农场”中。页面顶部有一个返回按钮（标签为1），页面中部显示了游戏内容和各种互动按钮。
# 2. 思考：为了购买雪地靴，需要退出“芭芭农场”模块。最有效的下一个单步交互操作是返回到主页面或上层页面。调用系统级返回操作或者点击页面顶部的返回按钮（标签为1）都可以达到目的，我选择调用系统级返回操作。
# 3. 操作：`back()`
#
# - 示例4（操作意图为“删除联系人‘张伟’”）：
# 1. 观察：当前界面显示的是通讯录应用的联系人列表。页面顶部有一个搜索栏，页面中部是按字母顺序排列的联系人列表。页面底部是“添加联系人”和“设置”两个选项。联系人列表中有一个名为“张伟”的联系人条目（标签为6）。
# 2. 思考：为了删除联系人“张伟”，需要向左滑动联系人“张伟”所在的条目（标签为6）以显示删除按钮。
# 3. 操作：`swipe(6, "left")`
#
# - 示例5（操作意图为“标记所有未读对话为已读”）：
# 1. 观察：当前界面显示的是聊天类应用的对话列表。页面顶部有一个搜索栏，页面中部显示的是和不同联系人的对话列表，其中部分对话条目带有未读消息标记。页面底部有“对话”、“通讯录”、“发现”、“我”四个选项。未读对话的标签分别为3、4、6、9。
# 2. 思考：为了标记所有未读对话为“已读”，需要从其中一个开始。按照从上到下的顺序，先标记和“陈国强”的对话条目（标签为3）为已读。因此，应该长按和“陈国强”的对话条目（标签为3）以显示标为已读的选项。
# 3. 操作：`long_press(3)`
#
# - 示例6（操作意图为“查看热榜”）：
# 1. 观察：当前界面显示的是一款知识类应用的热榜界面。页面顶部有“推荐”、“关注”和“热榜”三个标签，当前选中的是“热榜”。页面中部是当前热门的讨论条目。页面底部有一个控制栏，其中包括四个图标控件。从图标分析，这四个控件分别对应“主页”、“新建问题”、“会员信息”和“用户信息”。
# 2. 思考：目前已经处于热榜界面，操作意图已经达成，因此无需执行任何操作。
# 3. 操作：`finish()`
#
# - 示例7（操作意图为“查看‘李晓明’的朋友圈”）：
# 1. 观察：当前界面显示的是一款射击类游戏应用的游玩界面。页面中间是第三人称视角的游戏角色，他背着战斗背包并手持一把步枪。场景的远处有几处房屋和树。页面两侧有一些控件，对应不同的操作。
# 2. 思考：该应用为游戏应用，无朋友圈功能，因此无法执行任何操作以完成目标意图。
# 3. 操作：`finish()`"""


    return prompt


def get_reflect_prompt(instruction, clickable_infos1, clickable_infos2, width, height, keyboard1, keyboard2, summary,
                       action, add_info):
    prompt = f"These images are two phone screenshots before and after an operation. Their widths are {width} pixels and their heights are {height} pixels.\n\n"

    prompt += "In order to help you better perceive the content in this screenshot, we extract some information on the current screenshot through system files. "
    prompt += "The information consists of two parts, consisting of format: coordinates; content. "
    prompt += "The format of the coordinates is [x, y], x is the pixel from left to right and y is the pixel from top to bottom; the content is a text or an icon description respectively "
    prompt += "The keyboard status is whether the keyboard of the current page is activated."
    prompt += "\n\n"

    # prompt += "### Before the current operation ###\n"
    # prompt += "Screenshot information:\n"
    # for clickable_info in clickable_infos1:
    #     if clickable_info['text'] != "" and clickable_info['text'] != "icon: None" and clickable_info[
    #         'coordinates'] != (0, 0):
    #         prompt += f"{clickable_info['coordinates']}; {clickable_info['text']}\n"
    # prompt += "Keyboard status:\n"
    # if keyboard1:
    #     prompt += f"The keyboard has been activated."
    # else:
    #     prompt += "The keyboard has not been activated."
    # prompt += "\n\n"
    #
    # prompt += "### After the current operation ###\n"
    # prompt += "Screenshot information:\n"
    # for clickable_info in clickable_infos2:
    #     if clickable_info['text'] != "" and clickable_info['text'] != "icon: None" and clickable_info[
    #         'coordinates'] != (0, 0):
    #         prompt += f"{clickable_info['coordinates']}; {clickable_info['text']}\n"
    # prompt += "Keyboard status:\n"
    # if keyboard2:
    #     prompt += f"The keyboard has been activated."
    # else:
    #     prompt += "The keyboard has not been activated."
    # prompt += "\n\n"

    prompt += "### Current operation ###\n"
    prompt += f"The user\'s instruction is: {instruction}. You also need to note the following requirements: {add_info}. In the process of completing the requirements of instruction, an operation is performed on the phone. Below are the details of this operation:\n"
    prompt += "Operation thought: " + summary.split(" to ")[0].strip() + "\n"
    prompt += "Operation action: " + action
    prompt += "\n\n"

    prompt += "### Response requirements ###\n"
    prompt += "Now you need to output the following content based on the screenshots before and after the current operation:\n"
    prompt += "Whether the result of the \"Operation action\" meets your expectation of \"Operation thought\"?\n"
    prompt += "A: The result of the \"Operation action\" meets my expectation of \"Operation thought\".\n"
    prompt += "B: The \"Operation action\" results in a wrong page and I need to return to the previous page.\n"
    prompt += "C: The \"Operation action\" produces no changes."
    prompt += "\n\n"

    prompt += "### Output format ###\n"
    prompt += "Your output format is:\n"
    prompt += "### Thought ###\nYour thought about the question\n"
    prompt += "### Answer ###\nA or B or C"

    return prompt


def get_memory_prompt(insight):
    if insight != "":
        prompt = "### Important content ###\n"
        prompt += insight
        prompt += "\n\n"

        prompt += "### Response requirements ###\n"
        prompt += "Please think about whether there is any content closely related to ### Important content ### on the current page? If there is, please output the content. If not, please output \"None\".\n\n"

    else:
        prompt = "### Response requirements ###\n"
        prompt += "Please think about whether there is any content closely related to user\'s instrcution on the current page? If there is, please output the content. If not, please output \"None\".\n\n"

    prompt += "### Output format ###\n"
    prompt += "Your output format is:\n"
    prompt += "### Important content ###\nThe content or None. Please do not repeatedly output the information in ### Memory ###."

    return prompt


def get_process_prompt(instruction, thought_history, summary_history, action_history, completed_content, add_info):
    prompt = "### Background ###\n"
    prompt += f"There is an user\'s instruction which is: {instruction}. You are a mobile phone operating assistant and are operating the user\'s mobile phone.\n\n"

    if add_info != "":
        prompt += "### Hint ###\n"
        prompt += "There are hints to help you complete the user\'s instructions. The hints are as follow:\n"
        prompt += add_info
        prompt += "\n\n"

    if len(thought_history) > 1:
        prompt += "### History operations ###\n"
        prompt += "To complete the requirements of user\'s instruction, you have performed a series of operations. These operations are as follow:\n"
        for i in range(len(summary_history)):
            operation = summary_history[i].split(" to ")[0].strip()
            prompt += f"Step-{i + 1}: [Operation thought: " + operation + "; Operation action: " + action_history[
                i] + "]\n"
        prompt += "\n"

        prompt += "### Progress thinking ###\n"
        prompt += "After completing the history operations, you have the following thoughts about the progress of user\'s instruction completion:\n"
        prompt += "Completed contents:\n" + completed_content + "\n\n"

        prompt += "### Response requirements ###\n"
        prompt += "Now you need to update the \"Completed contents\". Completed contents is a general summary of the current contents that have been completed based on the ### History operations ###.\n\n"

        prompt += "### Output format ###\n"
        prompt += "Your output format is:\n"
        prompt += "### Completed contents ###\nUpdated Completed contents. Don\'t output the purpose of any operation. Just summarize the contents that have been actually completed in the ### History operations ###."

    else:
        prompt += "### Current operation ###\n"
        prompt += "To complete the requirements of user\'s instruction, you have performed an operation. Your operation thought and action of this operation are as follows:\n"
        prompt += f"Operation thought: {thought_history[-1]}\n"
        operation = summary_history[-1].split(" to ")[0].strip()
        prompt += f"Operation action: {operation}\n\n"

        prompt += "### Response requirements ###\n"
        prompt += "Now you need to combine all of the above to generate the \"Completed contents\".\n"
        prompt += "Completed contents is a general summary of the current contents that have been completed. You need to first focus on the requirements of user\'s instruction, and then summarize the contents that have been completed.\n\n"

        prompt += "### Output format ###\n"
        prompt += "Your output format is:\n"
        prompt += "### Completed contents ###\nGenerated Completed contents. Don\'t output the purpose of any operation. Just summarize the contents that have been actually completed in the ### Current operation ###.\n"
        prompt += "(Please use English to output)"

    return prompt
