"""
log management api requests functions and methods
"""

import io
import json
from pathlib import Path
from typing import Union, List, TextIO, BinaryIO, Optional
import warnings

import pandas as pd
from requests import Response

from pylana.decorators import expect_json, warn_for_interface_deprecation
from pylana.decorators import handle_response
from pylana.resources import ResourceAPI
from pylana.utils import create_case_semantics_from_df, \
    create_event_semantics_from_df


def _serialise_semantics(semantics: Union[str, list]):
    return \
        json.dumps(semantics) if not isinstance(semantics, str) else semantics


class LogsAPI(ResourceAPI):

    def list_logs(self, **kwargs) -> list:
        """List all logs that are available to the user.

        Args:
            **kwargs:
                Keyword arguments passed to requests functions.
            
        Returns:
            A list of log names.
        """    
        return self.list_resources('logs', **kwargs)

    @expect_json
    def list_user_logs(self, **kwargs) -> list:
        """List all logs owned by the user.

        Args:
            **kwargs:
                Keyword arguments passed to requests functions.
            
        Returns: 
            A list of log names.
        """
        return self.get('/api/users/' + self.user.user_id + '/logs', **kwargs)

    def get_log_ids(self, contains: str = '.*', **kwargs) -> List[str]:
        """Get all log ids which names are matched by the passed regular
        expression.

        Args:
            contains:
                A string denoting a regular expression
                matched against the log names.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            A list of strings denoting log ids.
        """
        return self.get_resource_ids('logs', contains, **kwargs)

    def get_log_id(self, contains: str, **kwargs) -> str:
        """Get id of a log by its name.

        The name needs to be unique, otherwise an exception is raised.

        Args:
            contains:
                A string denoting a regular expression
                matched against the log names.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            A string denoting the id of the log.
        """
        return self.get_resource_id('logs', contains, **kwargs)

    def describe_log(self, contains: str = None, log_id: str = None,
                     **kwargs) -> dict:
        """Get the description of log.

        Args:
            log_id:
                A string denoting the id of the log, takes precedence
                over contains.
            contains:
                A string denoting a regular expression matched against
                the log names, matching several names raises an exception.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            A dictionary denoting the log description.
        """
        return self.describe_resource('logs', contains, log_id, **kwargs)

    def upload_event_log(self, name,
                         log: str, log_semantics: Union[str, List[dict]],
                         case_attributes: Optional[str] = None,
                         case_attribute_semantics: Optional[Union[str, List[dict]]] = None,
                         **kwargs) \
            -> Response:
        """Upload an event log with prepared semantics.
        
        Args:
            name:
                A string denoting the name for the uploaded log.
            log:
                A string denoting the event log as csv.
            log_semantics:
                The event log semantics either serialised as a
                string or a list of dictionaries.
            case_attributes:
                (optional) A string denoting the case
                attributes as csv.
            case_attribute_semantics:
                (optional) The event case attributes semantics
                either serialised as a string or a list of
                dictionaries, required if case_attributes is
                passed.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            The requests response of the lana api call.
        """

        files_required = {
            'eventCSVFile': (name, log, 'text/csv')
        }
        semantics_required = {
            'eventSemantics': _serialise_semantics(log_semantics),
            'logName': name,
            'timeZone': "Europe/Berlin"
        }

        files = {
            **files_required,
            **{'caseAttributeFile': (name + '_case_attributes', case_attributes, 'text/csv')}
        } if case_attributes else files_required
        semantics = {
            **semantics_required,
            **{'caseSemantics': _serialise_semantics(case_attribute_semantics)}
        } if case_attribute_semantics else semantics_required

        return self.post('/api/logs/csv-case-attributes-event-semantics',
                         files=files, data=semantics, **kwargs)

    def upload_event_log_stream(self,
                                log: Union[TextIO, BinaryIO],
                                log_semantics: Union[list, str],
                                case: Optional[Union[TextIO, BinaryIO]] = None,
                                case_semantics: Optional[Union[list, str]] = None,
                                prefix: str = 'pylana-', **kwargs) -> Response:
        """Upload a log with prepared semantics by passing open streams.

        The log name is generated from hash value of the passed event log
        stream. We use the built-in hash function, so it can change when you
        restart the interpreter.

        WARNING: This method does not close the passed streams.

        Args:
            log:
                A string or binary stream denoting the event log.
            log_semantics:
                The event log semantics either serialised as a
                string or a list of dictionaries.
            case:
                (optional) A text or binary stream denoting the
                case attributes as csv.
            case_semantics:
                (optional) The event case attributes semantics
                either serialised as a string or a list of
                dictionaries, required if case_attributes is
                passed.
            prefix:
                (optional) A string denoting a prefix of the log name.
                Defaults to "pylana-".
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            The requests response of the lana api call.
        """

        name = f'{prefix}{hash(log)}'
        return self.upload_event_log(name, log.read(), log_semantics,
                                     case.read(), case_semantics, **kwargs)

    def upload_event_log_df(self, name: str, df_log: pd.DataFrame,
                            time_format: str, df_case: pd.DataFrame,
                            **kwargs) -> Response:
        """Upload an event log from pandas data frames with inferred semantics.

        For the passed event log data frame we expect at least the following
        columns:
        - "Case_ID" for the case id, any dtype
        - "Action" of dtype object for activities
        - "Start" of dtype datetime64 or object for the first timestamp
        The "Complete" column of type datetime64 or object is optional.

        For the passed case attributes we expect at last the columns "Case_ID"
        of any dtype.

        Types of other columns are inferred from their dtypes.

        Args:
            name:
                A string denoting the name under which the log is uploaded.
            df_log:
                A pandas data frame denoting the event log.
            time_format:
                A string denoting the timestamp format. Needs to match the
                string format of the "Start" and, if present, "Complete"
                columns. If either or both columns are of dtype datetime64,
                the time format needs to match its string representation.
                For a format definition, see
                https://docs.oracle.com/javase/8/docs/api/java/time/format/DateTimeFormatter.html#patterns
            df_case:
                (Optional) A pandas data frame denoting the case
                attributes.
            **kwargs:
                Keyword arguments passed to requests functions.

            Returns:
                The requests response of the lana api call.
        """

        event_semantics = create_event_semantics_from_df(df_log, time_format=time_format)
        case_semantics = create_case_semantics_from_df(df_case)

        return self.upload_event_log(name,
                                     log=df_log.to_csv(index=False),
                                     log_semantics=event_semantics,
                                     case_attributes=df_case.to_csv(index=False),
                                     case_attribute_semantics=case_semantics, **kwargs)

    def upload_event_log_file(self, name: str,
                              event_file_path: str, case_file_path: str,
                              event_semantics_path: str,
                              case_semantics_path: str, **kwargs) -> Response:
        """Upload an event log with case attributes by their path.

        Paths to semantic files have to be passed as well. All files are read
        in as binaries, the lana backend will try to infer the encoding.

        Args:
            name:
                A string denoting the name under which the
                log will be uploaded.
            event_file_path:
                A string denoting the path to the event log csv file.
            case_file_path:
                A string denoting the path to the case attribute csv file.
            event_semantics_path:
                A string denoting the path to the event log semantics
                json file.
            case_semantics_path:
                A string denoting the path to the case attributes semantics
                json file.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            The requests response of the lana api call.
        """
        with open(event_file_path, "rb") as event_file, \
                open(case_file_path, "rb") as case_file, \
                open(event_semantics_path) as event_semantics,\
                open(case_semantics_path) as case_semantics:

            files = {
                'eventCSVFile': (Path(event_file_path).name,
                                 event_file, 'text/csv'),
                'caseAttributeFile': (Path(case_file_path).name,
                                      case_file, 'text/csv'),
            }

            semantics = {
                'eventSemantics': event_semantics.read(),
                'caseSemantics': case_semantics.read(),
                'logName': name,
                'timeZone': "Europe/Berlin"
            }

            return self.post('/api/logs/csv-case-attributes-event-semantics',
                         files=files, data=semantics, **kwargs)

    def append_events_df(self, log_id,
                         df_log: pd.DataFrame, time_format: str, **kwargs) -> Response:
        """Append events to a log from a pandas data frame.

        For the passed event log data frame we expect at least the following
        columns:
        * "Case_ID" for the case id, any dtype
        * "Action" of dtype object for activities
        * "Start" of dtype datetime64 or object for the first timestamp
        The "Complete" column of type datetime64 or object is optional.

        Args:
            log_id:
                A string denoting the id of the log to which the events
                should be appended.
            df_log:
                A pandas data frame denoting the event log.
            time_format:
                A string denoting the timestamp format. Needs to match the
                string format of the "Start" and, if present, "Complete"
                columns. If either or both columns are of dtype datetime64,
                the time format needs to match its string representation.
                For a format definition, see
                https://docs.oracle.com/javase/8/docs/api/java/time/format/DateTimeFormatter.html#patterns
            **kwargs:
                Keyword arguments passed to requests functions.

            Returns:
                The requests response of the lana api call.
        """
        event_semantics = \
            create_event_semantics_from_df(df_log, time_format=time_format)

        files = {
            'eventCSVFile': ('event-file',
                             df_log.to_csv(index=False),
                             'text/csv')}
        semantics = {'eventSemantics': _serialise_semantics(event_semantics)}

        return self.post('/api/logs/' + log_id + '/csv', files=files,
                         data=semantics, **kwargs)

    def append_case_attributes_df(self, log_id,
                                  df_case: pd.DataFrame, **kwargs) -> Response:
        """Append case attributes to a log from a pandas data frame.

        For the passed case attributes we expect at least the case id
        column named "Case_ID".

        Args:
            log_id:
                A string denoting the id of the log for which the case
                attributes should be appended.
            df_case:
                A pandas data frame denoting the case attributes.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            The requests response of the lana api call.
        """
        case_semantics = create_case_semantics_from_df(df_case)

        files = {
            'caseAttributeFile': ('event-file',
                                  df_case.to_csv(index=False),
                                  'text/csv')}
        semantics = {'caseSemantics': _serialise_semantics(case_semantics)}

        return self.post('/api/logs/' + log_id + '/csv-case-attributes',
                         files=files, data=semantics, **kwargs)

    def delete_log(self, log_id: str, **kwargs) -> Response:
        """Delete a log by its id.
        
        Args:
            log_id:
                A string denoting the id of the log.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            The requests response of the lana api call.
        """
        return self.delete_resource('logs', log_id, **kwargs)

    def delete_logs(self, log_ids: List[str] = None, contains: str = None,
                    **kwargs) -> List[Response]:
        """Delete one or multiple logs.
        
        Args:
            log_ids:
                A list of strings denoting the ids of logs to delete. Tales
                precedence over contains.
            contains:
                A string denoting a regular expression matched against
                the log names.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            The requests response of the lana api call.
        """
        return self.delete_resources('logs', contains, log_ids, **kwargs)

    def request_event_csv(self, log_id: str,
                          mining_request: Optional[dict] = None,
                          **kwargs) -> Response:
        """Request the enriched event log.
        
        Args:
            log_id:
                A string denoting the id of the log.
            mining_request:
                (optional) A mining request data structure sent with
                request to filter down the log.
            **kwargs:
                Keyword arguments passed to requests functions.
            
        Returns:
            The requests response of the lana api call. The event log can be
            accessed under the text attribute of the response.
        """
        request_field = json.dumps(mining_request) if mining_request else json.dumps({
            'activityExclusionFilter': [],
            'includeHeader': True,
            'includeLogId': False,
            'logId': log_id,
            'edgeThreshold': 1,
            'traceFilterSequence': [], 'runConformance': True,
            'graphControl': {'sizeControl': 'Frequency', 'colorControl': 'AverageDuration'}})
        return self.get(f'/api/eventCsvWithFilter?request={request_field}', **kwargs)

    def get_event_log(self, log_name: str = None, log_id: str = None,
                      mining_request: Optional[dict] = None,
                      **kwargs) -> pd.DataFrame:
        """Get the enriched event log as a pandas data frame

        Only columns with time stamps are type cast, the other columns
        remain objects. If type casting is not desired, use to the method
        'request_event_csv'.
        
        Args:
            log_id:
                A string denoting the id of the log. Tales precedence
                over log_name.
            log_name:
                A string denoting the name of the log.
            mining_request:
                (optional) A mining request data structure sent with
                request to filter down the log.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            A data frame denoting the enriched log.
        """

        log_id = log_id or self.get_log_id(log_name)
        resp = self.request_event_csv(log_id, mining_request, **kwargs)
        if resp.status_code >= 400:
            return pd.DataFrame()
        csv_stream = io.BytesIO(resp.content)
        return pd.read_csv(csv_stream, dtype='object')

    @warn_for_interface_deprecation
    @handle_response
    def share_log(self, log_id: str, **kwargs) -> Response:
        """Share log with organisation.

        Args:
            log_id:
                A string denoting the log id.

        Returns:
            The requests response of the lana api call.
        """
        return self.share_resource("logs", log_id, **kwargs)

    @warn_for_interface_deprecation
    @handle_response
    def unshare_log(self, log_id: str, **kwargs) -> Response:
        """Un-share log with organisation.

        Args:
            log_id:
                A string denoting the log id.

        Returns:
            The requests response of the lana api call.
        """
        return self.unshare_resource("logs", log_id, **kwargs)

    def get_model_id_connected_to_log(
            self, contains: str = None, log_id: str = None, **kwargs) -> \
            Optional[str]:
        return (self.describe_log(contains, log_id, **kwargs)
                .get("connectedModel") or dict()) \
                .get("id")

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
            'eventCSVFile': (Path(logFile).name, open(logFile, 'rb'), 'text/csv'),
            'caseAttributesFile': (Path(caseAttributeFile).name, open(caseAttributeFile, 'rb'), 'text/csv'),
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
