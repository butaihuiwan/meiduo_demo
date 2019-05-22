from itsdangerous import TimedJSONWebSignatureSerializer, BadData
from django.conf import settings

def generate_access_token(openid):
    """

    :param openid:
    :return:
    """
    # 1. 创建对象

    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                                 expires_in=300)

    data = {
        'openid':openid

    }

    # 2.加密
    token = serializer.dumps(data) # bytes

    # 3.返回

    return token.decode() # str



def  check_access_token(access_token):
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                                 expires_in=300)
    try:
        data = serializer.loads(access_token)

    except BadData:
        return None
    else:
        return data.get('openid')

