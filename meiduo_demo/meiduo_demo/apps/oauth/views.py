import re

from QQLoginTool.QQtool import OAuthQQ
from django import http
from django.conf import settings
from django.contrib.auth import login

from django.db import DatabaseError
from django.shortcuts import redirect, render
from django.urls import reverse

from django.views import View
import logging

from django_redis import get_redis_connection

from meiduo_demo.apps.oauth.utils import generate_access_token, check_access_token
from user.models import User
from .models import OAuthQQUser

logger = logging.getLogger('django')

from meiduo_demo.utils.response_code import RETCODE



# 返回QQ登陆网址
class QQURLView(View):

    def get(self,request):

        next = request.GET.get('next')

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        login_url = oauth.get_qq_url()

        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok',
                                  'login_url':login_url})

# QQ登陆接口
class QQUserView(View):

    def get(self,request):

        # 接受code参数
        code = request.GET.get('code')
        # 判断code是否存在
        if not code:
            return http.HttpResponse('缺少code参数')

        # 创建对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            # 获取access_token
            access_token = oauth.get_access_token(code)

            # 获取openid
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('认证失败')

        # 判断表中是否存在
        try:
            oauth_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 从数据库中没有获取到该用户
            access_token = generate_access_token(openid)

            contents = {
                'access_token':access_token
            }
            return render(request,'oauth_callback.html',contents)



        else:
            # 从数据库中获取到该用户
            qq_user = oauth_user.user

            #实现状态保持

            login(request,qq_user)

            response = redirect(reverse('contents:index'))

            response.set_cookie('username',qq_user.username,
                                max_age=3600*24*15)

            return response



    def post(self,request):
        """美多商城用户绑定到openid"""
        # 1. 接受请求

        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code_client = request.POST.get('sms_code')
        access_token = request.POST.get('access_token')

        # 2. 校验参数
        if not all([mobile,password,sms_code_client]):
            return http.HttpResponseForbidden('缺少必传参数')

        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号')

        # 判断密码是否合格

        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位密码')

        # 判断短信验证码是否一致
        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_code')

        # 从redis中获取sms_code
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        if sms_code_server is None:
            return render(request,'oauth_callback.html',{'openid_errmsg':'无效的短信验证码'})

        if sms_code_client != sms_code_server.decode():
            return render(request,'oauth_callback.html',{'sms_code_errmsg':'输入的短信验证码错误'})

        openid = check_access_token(access_token)
        if not openid:
            return render(request, 'oauth_callback.html', {'openid_errmsg': '无效的openid'})

        # 保存注册数据

        try:
            user = User.objects.get(mobile=mobile)

        except User.DoesNotExist:

            # 用户不存在，新建用户
            user = User.objects.create_user(username=mobile,password=password,mobile=mobile)

        else:
            # 用户存在，检查用户密码
            if not user.check_password(password):
                return render(request,'oauth_callback.html',{'account_errmsg':'用户名密码错误'})

        # 将用户绑定openid

        try:
            OAuthQQUser.objects.create(openid=openid,user=user)
        except DatabaseError:
            return render(request,'oauth_callback.html',{'qq_login_errmsg':'QQ登陆失败'})

        # 实现状态保持
        login(request,user)

        # 绑定响应结果

        next = request.GET.get('next','/')
        response = redirect(next)

        # 登陆时用户名写入到cookie,有效期15天

        response.set_cookie('username',user.username,max_age=3600*24*15)

        return response



