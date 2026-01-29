from flask import abort
from globus_sdk import ConfidentialAppAuthClient, AuthClient, AccessTokenAuthorizer, GroupsClient, GlobusAPIError

from models.appconfig import AppConfig

def load_app_client(consortium: str) -> ConfidentialAppAuthClient:

    """
    Initiates a Globus app client, based on the consortium.
    :param consortium: identifies a Globus environment
    """
    cfg = AppConfig()

    if consortium == 'CONTEXT_HUBMAP':
        globus_client = cfg.getfield(key='GLOBUS_HUBMAP_CLIENT')
        globus_secret = cfg.getfield(key='GLOBUS_HUBMAP_SECRET')
    elif consortium == 'CONTEXT_SENNET':
        globus_client = cfg.getfield(key='GLOBUS_SENNET_CLIENT')
        globus_secret = cfg.getfield(key='GLOBUS_SENNET_SECRET')
    else:
        msg = f'Unknown consortium: {consortium}. Check the configuration file.'
        abort(400, msg)

    return ConfidentialAppAuthClient(globus_client, globus_secret)

def get_user_info(token):
    auth_client = AuthClient(authorizer=AccessTokenAuthorizer(token))
    return auth_client.oauth2_userinfo()

def get_group_info(token):
    authorizer = AccessTokenAuthorizer(token)
    groups_client = GroupsClient(authorizer=authorizer)
    try:
        return groups_client.get_my_groups()
    except GlobusAPIError as e:
        print(f"Error: {e.code} - {e.message}")
