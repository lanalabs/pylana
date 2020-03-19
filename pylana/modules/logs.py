import io
import json
import re
from typing import Union, List, TextIO, BinaryIO

import pandas as pd
from requests import Response

from pylana.modules.api import API
from pylana.semantics import create_case_semantics_from_df, create_event_semantics_from_df
from pylana.utils import expect_json
from pylana.utils import handle_response


def prepare_semantics(semantics: Union[str, list]):
    return json.dumps(semantics) if not isinstance(semantics, str) else semantics


class LogsAPI(API):

    @expect_json
    @handle_response
    def list_logs(self, **kwargs) -> list:
        """
        lists all logs that are available to the user

        Args:
            **kwargs: arguments passed to requests functions
        """
        return self.get('/api/logs', **kwargs)

    @expect_json
    @handle_response
    def list_user_logs(self, **kwargs) -> list:
        """
        list all logs owned bt the user

        Args:
            **kwargs: arguments passed to requests functions

        """
        return self.get('/api/users/' + self.user.user_id + '/logs', **kwargs)

    def get_log_ids(self, contains: str, **kwargs) -> list:
        """
        get all log ids which names are matched by the passed regular expression

        Args:
            contains: a regular expression matched against the log names
            application_key:
            host: backend host
            port: backend port

        Returns:
            a list of strings representing log ids
        """
        resp = self.get('/api/logs', **kwargs)

        rc = re.compile(contains)
        return [log['id'] for log in resp.json() if rc.search(log['name'])]

    def get_log_id(self, log_name: str, **kwargs) -> str:
        """
        get id of a log by its name

        name needs to be unique or an exception is raised
        """

        logs_matching = self.get_log_ids(log_name, **kwargs)

        try:
            [log_id] = logs_matching
        except ValueError as e:
            raise Exception(f'Found {len(logs_matching)} logs with the name {log_name}')

        return log_id

    @handle_response
    def upload_event_log_stream(self,
                                log: Union[TextIO, BinaryIO],
                                log_semantics: Union[list, str],
                                case: Union[TextIO, BinaryIO],
                                case_semantics: Union[list, str],
                                prefix='pylana-', **kwargs) -> Response:
        """
        upload a log with prepared semantics by passing open streams

        WARNING: does not close the passed streams
        """

        name = f'{prefix}{hash(log)}'
        return self.upload_event_log(name, log.read(), log_semantics,
                                     case.read(), case_semantics, **kwargs)

    @handle_response
    def upload_event_log(self, name,
                         log: str, log_semantics: Union[str, List[dict]],
                         case_attributes=None, case_attribute_semantics=None, **kwargs) \
            -> Response:
        """
        upload an event log with prepared semantics
        """

        files_required = {
            'eventCSVFile': (name, log, 'text/csv')
        }
        semantics_required = {
            'eventSemantics': prepare_semantics(log_semantics),
            'logName': name,
            'timeZone': "Europe/Berlin"
        }

        files = {
            **files_required,
            **{'caseAttributeFile': (name + '_case_attributes', case_attributes, 'text/csv')}
        } if case_attributes else files_required
        semantics = {
            **semantics_required,
            **{'caseSemantics': prepare_semantics(case_attribute_semantics)}
        } if case_attribute_semantics else semantics_required

        return self.post('/api/logs/csv-case-attributes-event-semantics',
                         files=files, data=semantics, **kwargs)

    @handle_response
    def upload_event_log_df(self, name: str,
                            df_log: pd.DataFrame, df_case: pd.DataFrame,
                            time_format: str, **kwargs) -> Response:
        """
        upload an event log from pandas dataframes with inferred semantics
        """

        df_events, event_semantics = create_event_semantics_from_df(df_log, time_format=time_format)
        df_cases, case_semantics = create_case_semantics_from_df(df_case)

        return self.upload_event_log(name,
                                     log=df_events.to_csv(index=False),
                                     log_semantics=event_semantics,
                                     case_attributes=df_cases.to_csv(index=False),
                                     case_attribute_semantics=case_semantics, **kwargs)

    @handle_response
    def append_events_df(self, log_id,
                         df_log: pd.DataFrame, time_format: str, **kwargs) -> Response:
        """
        append events to a log from a pandas dataframe with inferred semantics
        """
        df_events, event_semantics = create_event_semantics_from_df(df_log, time_format=time_format)

        files = {'eventCSVFile': ('event-file', df_events.to_csv(index=False), 'text/csv')}
        semantics = {'eventSemantics': prepare_semantics(event_semantics)}

        return self.post('/api/logs/' + log_id + '/csv', files=files, data=semantics, **kwargs)

    @handle_response
    def delete_log(self, log_id: str, **kwargs) -> Response:
        """
        delete a log by its id
        """
        return self.delete(f'/api/logs/{log_id}', **kwargs)

    def delete_logs(self, contains: str, **kwargs) -> List[Response]:
        """
        deletes one or multiple logs matching the passed regular expression
        """
        log_ids = self.get_log_ids(contains, **kwargs)
        return [self.delete_log(log_id) for log_id in log_ids]

    @handle_response
    def request_event_csv(self, log_id: str, **kwargs) -> Response:
        """
        request the enriched event csv
        """
        request_field = json.dumps({
            'activityExclusionFilter': [],
            'includeHeader': True,
            'includeLogId': False,
            'logId': log_id,
            'edgeThreshold': 1,
            'traceFilterSequence': [], 'runConformance': True,
            'graphControl': {'sizeControl': 'Frequency', 'colorControl': 'AverageDuration'}})
        return self.get(f'/api/eventCsvWithFilter?request={request_field}', **kwargs)

    def get_event_log(self, log_name: str = None, log_id: str = None, **kwargs) -> pd.DataFrame:
        """
        get the enriched event log as a pandas dataframe

        only columns with time stamps are type cast, the other columns remain objects
        """

        log_id = log_id or self.get_log_id(log_name)
        resp = self.get_event_csv(log_id)
        csv_stream = io.StringIO(resp.text)
        return pd.read_csv(csv_stream, dtype='object', **kwargs)

    # legacy methods
    # --------------

    def uploadEventLog(self, logFile, logSemantics):
        file = {
            'file': open(logFile, 'rb'),
        }

        semantics = {
            'eventSemantics': open(logSemantics).read(),
        }

        return self.post('/api/logs/csv', files=file, data=semantics)

    def uploadEventLogWithCaseAttributes(self, logFile, logSemantics,
                                         caseAttributeFile, caseAttributeSemantics, logName=None):

        files = {
            'eventCSVFile': (logFile.split('/')[-1], open(logFile, 'rb'), 'text/csv'),
            'caseAttributeFile': (caseAttributeFile.split('/')[-1], open(caseAttributeFile, 'rb'), 'text/csv'),
        }

        semantics = {
            'eventSemantics': open(logSemantics).read(),
            'caseSemantics': open(caseAttributeSemantics).read(),
            'logName': logName,
            'timeZone': "Europe/Berlin"
        }

        return self.post('/api/logs/csv-case-attributes-event-semantics',
                         files=files, data=semantics)

    def getUserLogs(self):
        return self.list_user_logs()

    def chooseLog(self, logName):
        userLogs = self.getUserLogs()
        logId = max([x['id'] for x in userLogs if x['name'] == logName])
        return logId

    @handle_response
    def appendEvents(self, logId: str, logFile, logSemantics):
        file = {'eventCSVFile': open(logFile, 'rb')}
        semantics = {'eventSemantics': open(logSemantics).read()}

        return self.post('/api/logs/' + logId + '/csv', files=file, data=semantics)

    @handle_response
    def appendAttributes(self, logId, caseAttributeFile, caseAttributeSemantics):
        file = {'caseAttributeFile': open(caseAttributeFile, 'rb')}
        semantics = {'caseSemantics': open(caseAttributeSemantics).read()}

        return self.post('/api/logs/' + logId + '/csv-case-attributes',
                         files=file, data=semantics)