from requests_oauthlib import OAuth2Session

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MailChannel(models.Model):
    _inherit = 'mail.channel'

    repo = fields.Char(default="")


class GithubProject(models.Model):
    _inherit = 'project.project'

    type = fields.Selection([('normal', 'Normal'), ('github', 'Github')], default="normal")
    link_connection = fields.Char(string='Connect to', compute='_compute_link')
    user_ids = fields.Many2many('res.users', string='Users')
    repository_id = fields.Many2one('github_project.repository', string='Repository',
                                    domain=lambda self: self._get_accessible_repositories())
    current_user_id = fields.Many2one('res.users', string='Owner', default=lambda self: self.env.user, readonly=True)

    def _get_accessible_repositories(self):
        return [('owner_id', '=', self.env.user.id)]

    @api.one
    @api.depends('type', 'current_user_id.github_access_token')
    def _compute_link(self):
        if self.type == 'github' and not self.current_user_id.github_access_token:
            web_hook = self.env['github_project.web_hook'].search([], limit=1)
            if web_hook:
                github = OAuth2Session(web_hook.client_id)
                authorization_url, state = github.authorization_url(web_hook.authorization_base_url)
                self.link_connection = authorization_url
        else:
            self.link_connection = '/get/repositories'

    def create_webhook_for_repo(self, repo_name):
        web_hook = self.env['github_project.web_hook'].search([], limit=1)
        web_hook = web_hook[0] if len(web_hook) > 0 else False

        if not web_hook:
            raise UserError(_("Please config Github Webhook!"))

        github = OAuth2Session(web_hook.client_id)

        query_access_token = '?access_token=' + self.env.user.github_access_token
        api_domain = 'https://api.github.com/'
        url_hooks = api_domain + 'repos/' + repo_name + '/hooks' + query_access_token

        data_send = {
            "name": "web",
            "active": True,
            "events": [
                "commit_comment",
                "delete",
                "deployment_status",
                "issues",
                "pull_request_review",
                "create",
                "fork",
                "issue_comment",
                "pull_request_review_comment",
                "release",
                "push",
                "pull_request"
            ],
            "config": {
                "url": self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                           .replace('http', 'https') + '/repositories/callback',
                "content_type": "json"
            }
        }

        github.post(url_hooks, json=data_send)

    @api.model
    def create(self, vals):
        if vals['type'] == 'github':
            if not self.env.user.github_access_token or not vals['repository_id']:
                raise UserError(_("Please click to Refresh to authenticated and get Repositories!"))

            # create a private channel
            github_user = self.env['res.users'].search([('name', 'ilike', 'Github')])

            if len(github_user) > 0:
                github_user = github_user[0]
            else:
                raise UserError(_("Please create a user with name is Github!"))

            partner_ids = self.env['res.users'].search([('id', 'in', vals['user_ids'][0][2])]).mapped('partner_id').ids
            repo_name = self.env['github_project.repository'].browse(vals['repository_id']).name

            self.env['mail.channel'].create({'name': vals['name'] + ' - Github Project',
                                             'repo': repo_name,
                                             'channel_partner_ids':
                                                 [(4, partner_id) for partner_id in partner_ids]
                                                 + [(4, github_user.partner_id.id)],
                                             'email_send': False
                                             })
            # create a web-hook for repository
            try:
                self.create_webhook_for_repo(repo_name)
            except Exception:
                raise UserError(_("Cannot connect to Github!"))

        return super(GithubProject, self).create(vals)


class GithubUser(models.Model):
    _inherit = 'res.users'

    project_ids = fields.Many2many('project.project', string='Projects')
    github_access_token = fields.Char(string='Github Access Token', default='')
    repository_ids = fields.One2many('github_project.repository', 'owner_id', string='Repositories')
    my_project_ids = fields.One2many('project.project', 'current_user_id', string='My Projects')


class Repository(models.Model):
    _name = 'github_project.repository'

    name = fields.Char(string='Name')
    url = fields.Char(string='Url')
    owner_id = fields.Many2one('res.users', string='Owner')


class WebHookApp(models.Model):
    _name = 'github_project.web_hook'

    name = fields.Char(string='Name', default='Github')
    client_id = fields.Char(string='Client ID', default='acc785f6b36dc847308b')
    client_secret = fields.Char(string='Client Secret', default='4b98519c3cc08073dc25d2c460e58e0fbe9895f5')
    authorization_base_url = fields.Char(string='Authorization Url',
                                         default='https://github.com/login/oauth/authorize?'
                                                 'scope=user%20public_repo%20admin:repo_hook')
    token_url = fields.Char(string='Token Url', default='https://github.com/login/oauth/access_token')

