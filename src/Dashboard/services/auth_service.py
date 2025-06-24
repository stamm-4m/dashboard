from Dashboard.models.user_model import get_user_by_username
from Dashboard.utils.security import check_password

def authenticate(username, password):
    user = get_user_by_username(username)
    if user and check_password(password, user['password']):
        print(user)
        return {"id": user['id'], "username": user['username'], "role": user['role']}
    return None
