import json

from requests_oauthlib import OAuth2Session

from odoo import http, tools, _
from odoo.http import request


class GithubController(http.Controller):
    @http.route(['/get/repositories'], type='http', auth="public", methods=['GET'], website=True)
    def get_repositories(self, **kwargs):
        access_token = request.env.user.github_access_token
        print(access_token)

        return "hello"

    @http.route(['/github/callback'], type='http', auth="public", methods=['GET'], website=True)
    def callback(self, **kwargs):
        code = kwargs.get('code')
        state = kwargs.get('state')
        web_hook = request.env['github_project.web_hook'].search([], limit=1)
        web_hook = web_hook[0] if len(web_hook) > 0 else False

        if web_hook and code and state:
            url = request.env['ir.config_parameter'].sudo().get_param('web.base.url') + \
                '/github/callback?code=' + str(code) + '&state=' + str(state)
            url = url.replace('http', 'https')
            try:
                github = OAuth2Session(web_hook.client_id)
                access_token = github.fetch_token(web_hook.token_url, client_secret=web_hook.client_secret,
                                                  authorization_response=url)
            except Exception as e:
                return str(e)

            access_token = access_token.get('access_token', '')
            if access_token:
                request.env.user.write({'github_access_token': access_token})
                query_access_token = '?access_token=' + str(access_token)
                api_domain = 'https://api.github.com/'
                res = github.get(api_domain + 'user' + query_access_token)
                print(res.content)
        return 'hello'
