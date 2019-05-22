import json
import re

from django import http
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout
from django.db import DatabaseError
from django.urls import reverse
from django_redis import get_redis_connection

from meiduo_demo.utils.response_code import RETCODE
from meiduo_demo.utils.views import LoginRequired, LoginRequiredJSONMixin
from .models import User
from django.shortcuts import render, redirect
import logging

logger = logging.getLogger('django')

# Create your views here.
from django.views import View

# 展示用户地址页面接口
class AddressView(View):
    """用户收货地址"""
    def get(self,request):

        return render(request,'user_center_site.html')







# 邮箱验证接口

class VerifyEmailView(View):
    """验证邮箱"""

    def get(self, request):
        # 1.接收参数
        token = request.GET.get('token')

        # 2.校验参数
        if not token:
            return http.HttpResponseBadRequest('缺少token值')
        user = User.check_cerify_emile_token(token)
        if not token:
            return http.HttpResponseForbidden('无效的token')
        # 3.修改emil_active的值为TRUE
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('激活邮件失败')
        # 返回邮箱验证结果
        return redirect(reverse('user:info'))


# 添加邮箱接口
class EmailView(LoginRequiredJSONMixin, View):
    def put(self, request):
        """

        :param request:
        :return:
        """
        # 1.接受参数
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 2.校验参数
        if not email:
            return http.HttpResponseForbidden('缺少email参数')
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('参数email有误')

        # 3.更新
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.HttpResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})

        # 发送邮箱
        from celery_tasks.email.tasks import send_verify_email
        # 异步发送验证邮件
        verify_url = request.user.generate_verify_email_url()
        send_verify_email.delay(email, verify_url)

        # 4.返回
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})


# 展示用户中心接口

class UserCenterInfoView(LoginRequired, View):

    def get(self, request):
        """

        :param request:
        :return:
        """
        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active

        }
        return render(request, 'user_center_info.html', context)


# 退出接口

class LogoutView(View):

    def get(self, request):
        """

        :param request:
        :return:
        """
        # 1.清理session
        logout(request)

        # 2.清除cookie中的username
        response = render(request, 'index.html')
        response.delete_cookie('username')

        # 3.返回
        return response


# 登陆接口
class LoginView(View):
    """获取登陆页面接口"""

    def get(self, request):
        return render(request, 'login.html')

    """进行登陆验证接口"""

    def post(self, request):
        """实现登陆验证逻辑"""
        # 1. 获取前端表单传参数据
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        # 2.校验参数，判断参数是否齐全
        if not all([username, password]):
            return http.HttpResponseForbidden('缺少必要参数')
        # 2.1 判断用户名是否是5-20个字符
        if not re.match(r'[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入正确的用户名')

        # 2.2 判断密码是否是8-20个字符
        if not re.match(r'[a-zA-Z0-9]{8,20}$', password):
            return http.HttpResponseForbidden('密码输入错误')

        # 认证登陆用户
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})

        # 4.实现状态保持
        login(request, user)

        # 5.返回响应
        # 判断是否勾选了记住用户名选项
        if remembered != 'on':
            request.session.set_expiry(0)

        else:
            request.session.set_expiry(None)

        response = render(request, 'index.html')
        response.set_cookie('username', user.username)

        return response


# 注册接口
class Register(View):

    def get(self, request):
        pass

        return render(request, 'register.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        sms_code_client = request.POST.get('sms_code')
        allow = request.POST.get('allow')

        if not all([username, password, password2, mobile, allow, sms_code_client]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        # 判断两次密码是否一致
        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')
        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')
        # 对短信验证码进行校验
        redis_conn = get_redis_connection('verify_code')
        redis_conn_server = redis_conn.get('sms_%s' % mobile)
        if redis_conn_server is None:
            return render(request, 'register.html', {'content': '输入验证码失效'})
        if sms_code_client != redis_conn_server.decode():
            return http.HttpResponseForbidden('输入短信验证码错误')

        # 判断是否勾选用户协议
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')

        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg': '注册失败'})

        login(request, user)
        # 响应注册结果
        # return http.HttpResponse('注册成功，重定向到首页')

        # 生成cookie
        response = render(request, 'index.html')
        response.set_cookie('username', user.username)

        return response


# 判断用户名是否重复注册
class UsernameCountView(View):

    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code': RETCODE.OK,
                                  'errmsg': 'ok',
                                  'count': 'count'})


# 判断手机号是否重复注册
class MobileCountView(View):
    """
    判断手机号是否重复注册
    """

    def get(self, request, mobile):
        """

        :param request: 请求对象
        : param mobile: 手机号
        :return: JSON
        """

        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({'code': RETCODE.OK,
                                  'errmsg': 'ok',
                                  'count': 'count'})
