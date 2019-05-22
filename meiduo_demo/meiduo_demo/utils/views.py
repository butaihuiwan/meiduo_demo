# 定义工具类：LoginRequired

# 继承自： View
from django import http
from django.contrib.auth.decorators import login_required
from django.views import View

from meiduo_demo.utils.response_code import RETCODE


class LoginRequired(object):
    """"验证用户是否登陆的工具类"""

    # 重写 as_view()函数
    # 在这个函数中, 对 as_view 进行装饰
    @classmethod
    def as_view(cls, **initkwargs):
        # 我们重写这个方法, 不想做任何的修改操作
        # 所以直接调用父类的 super().as_view() 函数.
        view = super().as_view()
        return login_required(view)

    # 我们自己的类视图, 让其继承自 LoginRequired


from django.utils.decorators import wraps


def login_required_json(view_func):
    """
    判断用户是否登录的装饰器，并返回 json
    :param view_func: 被装饰的视图函数
    :return: json、view_func
    """

    # 恢复 view_func 的名字和文档
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        # 如果用户未登录，返回 json 数据
        if not request.user.is_authenticated():
            return http.JsonResponse({'code': RETCODE.SESSIONERR, 'errmsg': '用户未登录'})
        else:
            # 如果用户登录，进入到 view_func 中
            return view_func(request, *args, **kwargs)

    return wrapper


class LoginRequiredJSONMixin(object):
    """验证用户是否登陆并返回 json 的扩展类"""

    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return login_required_json(view)

#
# class LoginRequiredJSONMixin(object):
#     """验证用户是否登陆并返回JSON的扩展类"""
#
#     @classmethod
#     def as_view(cls, **initkwargs):
#         view = super().as_view(**initkwargs)
#
#         return login_required_json(view)
