import datetime
import random
import uuid

# OBJECTIVES TODO:
# 1) Read the code and understand it.
# 2) Read the code again and understand it better.
# 3) Feel free to do 1 and 2 however many times you feel like.
# 4) Complete the SyncService implementation. Note that the SyncService.onMessage and SyncService.__init__ function signature must not be altered.

_DATA_KEYS = ["a", "b", "c"]

class Device:

    def __init__(self, id):
        self._id = id
        self.records = []
        self.sent = []

    def obtainData(self) -> dict:
        """Returns a single new datapoint from the device.
        Identified by type `record`. `timestamp` records when the record was sent, and `dev_id` is the device id.
        `data` is the data collected by the device."""
        if random.random() < 0.4:
            # Sometimes there's no new data
            return {}

        rec = {
            'type': 'record',
            'timestamp': datetime.datetime.now().isoformat(),
            'dev_id': self._id,
            'data': {kee: str(uuid.uuid4()) for kee in _DATA_KEYS}
        }
        self.sent.append(rec)
        return rec
#   
    def probe(self) -> dict:
        """Returns a probe request to be sent to the SyncService.
        Identified by type `probe`. `from` is the index number from which the device is asking for the data."""
        if random.random() < 0.5:
            # Sometimes the device forgets to probe the SyncService
            return {}
        return {'type': 'probe', 'dev_id': self._id, 'from': len(self.records)}

    def onMessage(self, data: dict):
        """Receives updates from the server"""
        if random.random() < 0.6:
            # Sometimes devices make mistakes. Let's hope the SyncService handles such failures.
            return

        if data is not None and data['type'] == 'update':
            # had to add "is not None", as the file was throwing a NoneType error with this line
            _from = data['from'] 
            if _from > len(self.records):
                 ## Either already updated data on the device,
                 ## or an error in the device, as more records stored than that on server
                return
            self.records = self.records[:_from] + data['data']

class SyncService:

    def __init__(self):
        ## vairable introduced to store synced data at server and facilitate synchronisation among different devices
        self.synced_data = []

    def onMessage(self, data: dict):
        """Handle messages received from devices.
        Return the desired information in the correct format (type `update`, see Device.onMessage and testSyncing to understand format intricacies)
        in response to a `probe`.
        No return value required on handling a `record`."""

        if 'type' in data and data['type'] == 'record':
            ##New record obtained by a device
            new_rec = {'timestamp': data['timestamp'], 'dev_id': data['dev_id'], 'data': data['data']} 
            ##Storing the essential key-value pairs
            self.synced_data.append(new_rec) 
            ##Appending the new record to synced_data
            return
        
        elif 'type' in data and data['type'] == 'probe': ##Probe request by some device
            start = data['from']    ##the index value from where the requesting device needs to be updated
            server_length = len(self.synced_data)
            if server_length > 0 and (start <= server_length - 1):
                ##When there is a requirement for updation, the requesting device has lesser records
                return {'type': 'update', 'data': self.synced_data[ start : ], 'from': start} 
                ##sending appropriate records, index start(labelled by key 'from') till the end of the list
            else: 
                #When synced_data is empty, no record stored yet
                return {'type': 'update', 'data': [], 'from': -1} 
                ##returning an empty list, as no data in server yet, nothing to be added,
                ## -1 like a placeholder for 'from' in this case
        else:
            pass

def testSyncing():
    devices = [Device(f"dev_{i}") for i in range(10)]
    syn = SyncService()

    _N = int(1e6)

    for i in range(_N):
        for _dev in devices:
            syn.onMessage(_dev.obtainData()) 
            ## data-creation and adding to server randomly
            _dev.onMessage(syn.onMessage(_dev.probe())) 
            ## (probability based) probe requests to server, followed by message and updations(if needed)
    done = False
    while not done:
        for _dev in devices:
            _dev.onMessage(syn.onMessage(_dev.probe())) 
            ## iterative probing till it is ensured that all records present on all devices
        num_recs = len(devices[0].records)
        done = all([len(_dev.records) == num_recs for _dev in devices])

    ver_start = [0] * len(devices) 
    ## a reference list to compare number of records on each device's 'sent' 
    ## with the records it sent as per storage across devices

    for i, rec in enumerate(devices[0].records): 
        ## creating an iterable of records of devices[0]
        _dev_idx = int(rec['dev_id'].split("_")[-1]) 
        ## obtaining the index of the device that sent this record
        assertEquivalent(rec, devices[_dev_idx].sent[ver_start[_dev_idx]]) 
        ## comparing that device's 'sent' with the record in storage
        for _dev in devices[1:]:
            assertEquivalent(rec, _dev.records[i]) 
            ## checking if the record is the same on all devices(devices[0] already checked)
        ver_start[_dev_idx] += 1 
        ## incrementing the index of 'sent'-record for a device with index _dev_idx 

def assertEquivalent(d1: dict, d2: dict): ## checks the equivalence of two records
    assert d1['dev_id'] == d2['dev_id']
    assert d1['timestamp'] == d2['timestamp']
    for kee in _DATA_KEYS:
        assert d1['data'][kee] == d2['data'][kee]

testSyncing()