from requests_oauthlib import OAuth2Session

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class GithubProject(models.Model):
    _inherit = 'project.project'

    test = fields.Char()
    type = fields.Selection([('normal', 'Normal'), ('github', 'Github')], default="normal")
    link_connection = fields.Char(string='Connect to', compute='_compute_link')
    user_ids = fields.Many2many('res.users', string='Users')
    repository_id = fields.Many2one('github_project.repository', string='Repository', ondelete='cascade',
                                    domain=lambda self: self._get_accessible_repositories())
    current_user_id = fields.Many2one('res.users', string='Owner', default=lambda self: self.env.user, readonly=True)

    def _get_accessible_repositories(self):
        return [('owner_id', '=', self.current_user_id)]

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

    @api.model
    def create(self, vals):
        if vals['type'] == 'github':
            admin = self.search([('id', '=', vals['admin_id'])])
            if not admin.github_access_token:
                raise UserError(_("Please click to Github to authenticate!"))
        return super(GithubProject, self).create(vals)


class GithubUser(models.Model):
    _inherit = 'res.users'

    project_ids = fields.Many2many('project.project', string='Projects')
    github_access_token = fields.Char(string='Github Token', default='')
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


class GithubChannel(models.Model):
    _inherit = 'mail.channel'

    pin = fields.Boolean(default=False)

