# 定义工具类：LoginRequired

# 继承自： View
from django.contrib.auth.decorators import login_required
from django.views import View


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
