#

import datetime
import json

from exchangelib import Account, Configuration, DELEGATE, Mailbox, Attendee, CalendarItem, EWSDateTime, OAUTH2, \
    OAuth2AuthorizationCodeCredentials
from exchangelib.items import SEND_TO_ALL_AND_SAVE_COPY
from msal import PublicClientApplication
from oauthlib.oauth2 import OAuth2Token

from credentials import *

################################################################
# INPUT
primary_smtp_address = 'x'  # needs to be an account
organizer = 'x'  # should be the same as primary_smtp_address

client_id = 'x'
tenant_id = 'x'
authority = f'https://login.microsoftonline.com/{tenant_id}/'
################################################################


class EWS:
    def __init__(self):
        app = PublicClientApplication(client_id=client_id, authority=authority)
        token = app.acquire_token_by_username_password(username=agent_user,
                                                       password=agent_password,
                                                       scopes=['https://outlook.office.com/EWS.AccessAsUser.All'])
        credentials = OAuth2AuthorizationCodeCredentials(access_token=OAuth2Token(token))
        config = Configuration(server='outlook.office.com', credentials=credentials, auth_type=OAUTH2)
        self.cert_account = Account(primary_smtp_address=primary_smtp_address, access_type=DELEGATE, config=config)

    def search_calendar(self, officer_tag, date):
        cal_items = self.cert_account.calendar.filter(
            start__gte=EWSDateTime.from_datetime(
                datetime.datetime(year=date.year, month=date.month, day=date.day, hour=0)).
            astimezone(self.cert_account.default_timezone),
            end__lte=EWSDateTime.from_datetime(
                datetime.datetime(year=date.year, month=date.month, day=date.day, hour=23)).
            astimezone(self.cert_account.default_timezone),
        )

        for item in cal_items.order_by('start'):
            if f"{officer_tag} - CERT Officer" == item.subject:
                return True
        return False

    def create_officer_invite(self, officer_mail: str, officer_tag: str, date: datetime.date):
        if self.search_calendar(officer_tag=officer_tag, date=date):
            print(f'[WARNING] Duplication on {date} for {officer_tag}')
            return

        item = CalendarItem(
            account=self.cert_account,
            folder=self.cert_account.calendar,
            start=EWSDateTime.from_datetime(datetime.datetime(year=date.year,
                                                              month=date.month,
                                                              day=date.day,
                                                              hour=9)).astimezone(self.cert_account.default_timezone),
            end=EWSDateTime.from_datetime(datetime.datetime(year=date.year,
                                                            month=date.month,
                                                            day=date.day,
                                                            hour=17)).astimezone(self.cert_account.default_timezone),
            subject=f"{officer_tag} - CERT Officer",
            reminder_minutes_before_start=15,
            reminder_is_set=True,
            organizer=organizer,
            required_attendees=[Attendee(mailbox=Mailbox(email_address=officer_mail))]
        )

        item.is_response_requested = False

        item.save(send_meeting_invitations=SEND_TO_ALL_AND_SAVE_COPY)
        print(f"[INFO] Created CalendarItem {date} for {officer_tag}")


def main():
    officer_selection = json.load(open("../data/officer_selection.json"))
    if not officer_selection:
        raise Exception('[WARNING] There is no officer selection data')
    
    officer_static = json.load(open("../data/officer_static.json"))
    if not officer_static:
        raise Exception('[WARNING] There is no officer static data')
    
    officer_map = {officer.get('name'): officer for officer in officer_static}

    cert_mailbox = EWS()

    for day, selected_officers in officer_selection.items():
        for selected_officer in selected_officers:
            officer_data = officer_map.get(selected_officer)
            if not officer_data:
                raise Exception(f'[WARNING] Selected officer ({selected_officer}) not found')

            cert_mailbox.create_officer_invite(officer_tag=officer_data.get('tag'),
                                               officer_mail=officer_data.get('mail'),
                                               date=datetime.datetime.strptime(day, '%Y-%m-%d').date())


if __name__ == "__main__":
    main()
