import datetime as dt
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import myles_common as common


class JobLeaseRepair(unittest.TestCase):
    def test_lease_can_transfer_and_clear_pid_without_argument_collision(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(common,'DB_PATH',Path(folder)/'test.db'):
            common.init_db()
            con=common.connect()
            con.execute("INSERT INTO jobs(id,prompt,source,state,phase,created_at,updated_at,workspace) VALUES(?,?,?,?,?,?,?,?)",('lease','test','test','pending','pending',common.now_iso(),common.now_iso(),folder))
            con.commit();con.close()
            self.assertTrue(common.claim_job_for_launch('lease'))
            self.assertTrue(common.assign_job_runner('lease',100))
            self.assertIsNotNone(common.get_job('lease')['started_at'])
            self.assertTrue(common.set_job_if_owned('lease',100,runner_pid=101))
            self.assertFalse(common.set_job_if_owned('lease',100,phase='wrong_worker'))
            self.assertTrue(common.set_job_if_owned('lease',101,state='completed',runner_pid=None))

    def test_launching_with_fresh_heartbeat_still_times_out(self):
        old=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(seconds=90)).isoformat()
        row={'state':'running','phase':'launching','runner_pid':100,'created_at':old,'started_at':None,'heartbeat_at':common.now_iso()}
        with patch.object(common,'pid_alive',return_value=True),patch.object(common,'load_config',return_value={'stall_no_heartbeat_seconds':60,'stall_no_progress_seconds':300}):
            truth=common.job_truth(row)
        self.assertEqual(truth['truth_state'],'stalled')
        self.assertIn('startup',truth['stall_reasons'][0])

if __name__=='__main__':unittest.main()
