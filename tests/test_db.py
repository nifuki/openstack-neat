# Copyright 2012 Anton Beloglazov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mocktest import *
from pyqcy import *

import neat.db_utils as db_utils


class Db(TestCase):

    @qc(1)
    def insert_select():
        db = db_utils.init_db('sqlite:///:memory:')
        db.vms.insert().execute(uuid='test')
        assert db.vms.select().execute().first()['uuid'] == 'test'
        db.vm_resource_usage.insert().execute(vm_id=1, cpu_mhz=1000)
        assert db.vm_resource_usage.select().execute().first()['cpu_mhz'] == 1000

    @qc(10)
    def select_cpu_mhz_for_vm(
        uuid=str_(of='abc123-', min_length=36, max_length=36),
        cpu_mhz=list_(of=int_(min=0, max=3000), min_length=0, max_length=10),
        n=int_(min=1, max=10)
    ):
        db = db_utils.init_db('sqlite:///:memory:')
        result = db.vms.insert().execute(uuid=uuid)
        vm_id = result.inserted_primary_key[0]
        for mhz in cpu_mhz:
            db.vm_resource_usage.insert().execute(
                vm_id=vm_id,
                cpu_mhz=mhz)
        assert db.select_cpu_mhz_for_vm(uuid, n) == cpu_mhz[:n]

    @qc(10)
    def select_vm_id(
        uuid1=str_(of='abc123-', min_length=36, max_length=36),
        uuid2=str_(of='abc123-', min_length=36, max_length=36)
    ):
        db = db_utils.init_db('sqlite:///:memory:')
        result = db.vms.insert().execute(uuid=uuid1)
        vm_id = result.inserted_primary_key[0]
        assert db.select_vm_id(uuid1) == vm_id
        assert db.select_vm_id(uuid2) == vm_id + 1

    @qc(10)
    def insert_cpu_mhz(
        vms=dict_(
            keys=str_(of='abc123-', min_length=36, max_length=36),
            values=tuple_(int_(min=1, max=3000),
                          list_(of=int_(min=1, max=3000),
                                min_length=0, max_length=10)),
            min_length=0, max_length=5
        )
    ):
        db = db_utils.init_db('sqlite:///:memory:')
        initial_data = []
        data_to_submit = {}
        final_data = {}

        for uuid, data in vms.items():
            vm_id = db.select_vm_id(uuid)
            data_to_submit[uuid] = data[0]
            final_data[uuid] = list(data[1])
            final_data[uuid].append(data[0])
            for cpu_mhz in data[1]:
                initial_data.append({'vm_id': vm_id,
                                     'cpu_mhz': cpu_mhz})
        if initial_data:
            db.vm_resource_usage.insert().execute(initial_data)

        db.insert_cpu_mhz(data_to_submit)

        for uuid, data in final_data.items():
            assert db.select_cpu_mhz_for_vm(uuid, 11) == data