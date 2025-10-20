from http import HTTPStatus
import dashscope
from dashscope import MultiModalConversation
from utils.draw import color_log

def query_qwen_vl(messages, logger, model_name="qwen-vl-max"):
    for message in messages:
        for content in message["content"]:
            if "text" in content:
                color_log(content["text"], logger, 'green')

    response = MultiModalConversation.call(
        model=model_name,
        messages=messages,
    )

    if response.status_code != HTTPStatus.OK:
        print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))

    role, content = response['output']['choices'][0]['message']['role'], \
    response['output']['choices'][0]['message']['content'][0]["text"]

    color_log(content, logger, 'blue')

    return role, content

def query_qwen2_api(messages, logger, model_name="qwen2-72b-instruct"):
    for message in messages:
        color_log(message["content"], logger, 'green')

    response = dashscope.Generation.call(
        model_name,
        messages=messages,
        result_format='message',
    )

    if response.status_code != HTTPStatus.OK:
        print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))

    role, content = response.output.choices[0].message.role, response.output.choices[0].message.content
    color_log(content, logger, 'blue')

    return role, content
    