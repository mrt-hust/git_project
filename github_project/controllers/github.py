import json
from requests_oauthlib import OAuth2Session
from odoo import http, tools, _
from odoo.http import request


class GithubController(http.Controller):
    @http.route(['/get/repositories'], type='http', auth="public", methods=['GET'], website=True)
    def get_repositories(self, **kwargs):
        access_token = request.env.user.github_access_token
        web_hook = request.env['github_project.web_hook'].search([], limit=1)
        web_hook = web_hook[0] if len(web_hook) > 0 else False

        if not web_hook:
            return "ERROR! No config Github-Webhook!"

        try:
            github = OAuth2Session(web_hook.client_id)
        except Exception as e:
            return str(e)

        request.env.user.write({'github_access_token': access_token})
        query_access_token = '?access_token=' + str(access_token)
        api_domain = 'https://api.github.com/'
        res = github.get(api_domain + 'user' + query_access_token)
        data = json.loads(res.content.decode('utf-8'))
        # Get Repositories
        repos = data.get('repos_url', '')
        if repos:
            res = github.get(repos)
            repo_data = json.loads(res.content.decode('utf-8'))

            repo_list = []
            for repo in repo_data:
                repo_list.append({'url': repo.get('html_url'), 'name': repo.get('full_name'),
                                  'owner_id': request.env.user.id})

            current_repositories = request.env['github_project.repository']\
                .search([('owner_id', '=', request.env.user.id)])
            existed_repositories = {r.name: r for r in current_repositories}

            for r in repo_list:
                existed_r = existed_repositories.get(r['name'])
                if existed_r:
                    existed_r.write(r)
                else:
                    request.env['github_project.repository'].create(r)

        return request.render("github_project.success")

    @http.route(['/github/callback'], type='http', auth="public", methods=['GET'], website=True)
    def callback(self, **kwargs):
        code = kwargs.get('code')
        state = kwargs.get('state')
        web_hook = request.env['github_project.web_hook'].search([], limit=1)
        web_hook = web_hook[0] if len(web_hook) > 0 else False

        if not web_hook:
            return "ERROR! No config Github-Webhook!"

        try:
            github = OAuth2Session(web_hook.client_id)
        except Exception as e:
            return str(e)

        if not code or not state:
            return "Error during get access token, please try again!"

        url = request.env['ir.config_parameter'].sudo().get_param('web.base.url') + \
            '/github/callback?code=' + str(code) + '&state=' + str(state)
        url = url.replace('http', 'https')
        try:
            access_token = github.fetch_token(web_hook.token_url, client_secret=web_hook.client_secret,
                                              authorization_response=url)
        except Exception as e:
            return str(e)

        access_token = access_token.get('access_token', '')

        request.env.user.write({'github_access_token': access_token})
        query_access_token = '?access_token=' + str(access_token)
        api_domain = 'https://api.github.com/'
        res = github.get(api_domain + 'user' + query_access_token)
        data = json.loads(res.content.decode('utf-8'))

        # Get Repositories
        repos = data.get('repos_url', '')
        if repos:
            res = github.get(repos)
            repo_data = json.loads(res.content.decode('utf-8'))

            repo_list = []
            for repo in repo_data:
                repo_list.append({'url': repo.get('html_url'), 'name': repo.get('full_name'),
                                  'owner_id': request.env.user.id})

            current_repositories = request.env['github_project.repository'] \
                .search([('owner_id', '=', request.env.user.id)])
            existed_repositories = {r.name: r for r in current_repositories}

            for r in repo_list:
                existed_r = existed_repositories.get(r['name'])
                if existed_r:
                    existed_r.write(r)
                else:
                    request.env['github_project.repository'].create(r)
        return request.render("github_project.success")

    @http.route(['/repositories/callback'], type='json', auth="public", methods=['POST'])
    def repo_callback(self, **kwargs):
        data = request.jsonrequest
        commit = data.get('head_commit', False)
        if not commit:
            return False
        url = commit['url']
        author = commit['author']['username']
        repo = data['repository']['full_name']
        repo_url = data['repository']['url']
        author_url = 'https://github.com/' + author
        message = commit['message']
        notification = _(
            '<div class="o_mail_notification">'
            ' New <a href="%s" target="_blank"><b>#commit</b></a> by <a href="%s" target="_blank"><b>%s</b></a>'
            ' on <a href="%s" target="_blank"><b>%s</b></a>'
            '<br><i>%s</i>'
            '</div>') % (url, author_url, author, repo_url, repo, message)
        git_user = request.env['res.users'].sudo().search([('name', 'ilike', 'Github')])[0]
        channels = request.env['mail.channel'].sudo().search([('repo', 'ilike', repo)])
        print(channels)
        for channel in channels:
            ms = channel.message_post(body=notification, message_type="comment", subtype="mail.mt_comment",
                                      author_id=git_user.partner_id.id)
            print(ms)
        return True
