import re

from django.contrib.auth.backends import ModelBackend
from .models import User


def get_user_by_account(account):
    """ 根据account查询用户
    :param account: 用户名或者手机号
    :return: user"""
    try:
        if re.match(r'^1[3-9]\d{9}$',account):
            user = User.objects.get(mobile = account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user




class UsernameMobileAuthBackend(ModelBackend):
    """自定义用户认证后端"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """重写认证方法，实现用户名和手机号登陆功能
        :param request: 请求对象
        :param username: 用户名
        :param password: 密码
        :param kwargs: 其他参数
        :return: user"""
        user = get_user_by_account(username)

        # 校验user是否存在并校验密码是否正确
        if user and user.check_password(password):
            return user




