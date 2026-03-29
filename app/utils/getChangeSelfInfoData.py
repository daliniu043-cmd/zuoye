
from app.models import User


# 修改个人信息
def changeSelfInfo(username, formData, file):
    user = User.objects.get(username=username)
    user.address = formData['address']
    user.sex = formData['sex'] if formData['sex'] else ''  # 如果未选择性别，则将其设置为None
    if formData['textarea']:
        user.textarea = formData['textarea']
    if file.get('avatar') != None:
        user.avatar = file.get('avatar')

    user.save()


# 修改密码
def changePassword(userInfo, passwordInfo):
    # 检查oldPwd, newPwd, newPwdConfirm是否为空
    if not passwordInfo.get('oldPassword'):
        return '原始密码不能为空'
    if not passwordInfo.get('newPassword'):
        return '新密码不能为空'
    if not passwordInfo.get('newPasswordConfirm'):
        return '确认新密码不能为空'

    oldPwd = passwordInfo['oldPassword']
    newPwd = passwordInfo['newPassword']
    newPwdConfirm = passwordInfo['newPasswordConfirm']

    # 检查原始密码是否正确
    if oldPwd != userInfo.password:
        return '原始密码不正确'

    # 检查两次输入的新密码是否一致
    if newPwd != newPwdConfirm:
        return '两次新密码不一致'

    # 检查用户是否存在
    try:
        user = User.objects.get(username=userInfo.username)
    except User.DoesNotExist:
        return '用户不存在'

    # 更新密码
    user.password = newPwdConfirm
    user.save()
