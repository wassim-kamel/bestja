# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions


class Application(models.Model):
    _inherit = 'offers.application'

    # preliminary -> first stage of recruitment
    preliminary = fields.Boolean(default=True)

    def _auto_init(self, cr, context=None):
        # Overwrite sql constraints from parent.
        # Done here as a workaround for issue #3957 in Odoo
        # https://github.com/odoo/odoo/issues/3957
        self._sql_constraints = [
            ('user_offer_uniq', 'unique("user", "offer", "preliminary")', 'User can apply for an offer only once!')
        ]
        super(Application, self)._auto_init(cr, context)

    @api.one
    def _send_message_new(self):
        if self.preliminary and not self.sudo().offer.is_owned_by_moderator():
            # when application has just been created
            # send message to admin about new application
            self.send_group(
                template='bestja_application_moderation.msg_new_application_admin',
                group='bestja_offers_moderation.offers_moderator',
            )
        else:
            super(Application, self)._send_message_new()

    @api.one
    def confirm_meeting(self):
        if self.preliminary:
            self.current_meeting_state = 'accepted'

            self.send_group(
                template='bestja_offers.msg_application_meeting_accepted',
                group='bestja_offers_moderation.offers_moderator',
                sender=self.env.user,
            )
        else:
            super(Application, self).confirm_meeting()

    @api.one
    def reject_meeting(self):
        if self.preliminary:
            self.current_meeting_state = 'rejected'

            self.send_group(
                template='bestja_offers.msg_application_meeting_rejected',
                group='bestja_offers_moderation.offers_moderator',
                sender=self.env.user,
            )
        else:
            super(Application, self).reject_meeting()

    @api.model
    def create(self, vals):
        record = super(Application, self).create(vals)
        record_sudo = record.sudo()

        # if the project is managed / coordinated by admin,
        # automatically move the application to the second
        # stage of recruitment.
        if record_sudo.offer.is_owned_by_moderator():
            record_sudo.preliminary = False
        return record

    @api.one
    def action_post_accepted(self):
        if self.preliminary:
            if not self.user_has_groups('bestja_offers_moderation.offers_moderator'):
                raise exceptions.ValidationError("Nie masz uprawnień aby wykonać tę akcję!")

            # "Move" to the second stage of recruitment
            application = self.sudo().create({
                'user': self.user.id,
                'offer': self.offer.id,
                'preliminary': False,
            })
            # Send message that user was moved to the second stage, to user
            application.send(
                template='bestja_application_moderation.msg_application_second_stage',
                recipients=self.user,
                record_name=self.offer.name,
            )
        else:
            super(Application, self).action_post_accepted()

    @api.one
    def action_post_unaccepted(self):
        if self.preliminary:
            raise exceptions.ValidationError(
                "Aplikacja została przesłana do organizacji. Zmiana jej statusu nie jest już możliwa."
            )
        else:
            super(Application, self).action_post_unaccepted()


class Offer(models.Model):
    _inherit = 'offer'

    @api.multi
    def is_owned_by_moderator(self):
        self.ensure_one()

        coordinator = self.sudo().organization.coordinator
        manager = self.sudo().project.manager
        group = 'bestja_offers_moderation.offers_moderator'

        return self.sudo(coordinator.id).user_has_groups(group) or \
            (manager and self.sudo(manager.id).user_has_groups(group))
