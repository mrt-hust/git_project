import json

from requests_oauthlib import OAuth2Session

from odoo import http, tools, _
from odoo.http import request


class GithubController(http.Controller):
    @http.route(['/get/repositories'], type='http', auth="public", methods=['GET'], website=True)
    def get_repositories(self, **kwargs):
        access_token = request.env.user.github_access_token
        print(access_token)
        request.env['mail.channel'].create({'name': 'github7',
                                            'privacy': 'private',
                                            'channel_partner_ids': [(4, request.env.user.partner_id.id), (4, 45)],
                                            'email_send': False,
                                            'pin': True})

        return "hello"

    @http.route(['/github/callback'], type='http', auth="public", methods=['GET'], website=True)
    def callback(self, **kwargs):
        code = kwargs.get('code')
        state = kwargs.get('state')
        web_hook = request.env['github_project.web_hook'].search([], limit=1)
        if web_hook and code and state:
            url = request.env['ir.config_parameter'].sudo().get_param('web.base.url') + \
                '/github/callback?code=' + str(code) + '&state=' + str(state)
            github = OAuth2Session(web_hook.client_id)
            access_token = github.fetch_token(web_hook.token_url, client_secret=web_hook.client_secret,
                                              authorization_response=url)
            print(access_token)
        return access_token
