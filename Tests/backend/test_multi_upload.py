import io
import os
import shutil
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_upload_multiple_files_creates_outputs():
    files = [
        ('files', ('test1.laz', io.BytesIO(b'dummy1'), 'application/octet-stream')),
        ('files', ('test2.laz', io.BytesIO(b'dummy2'), 'application/octet-stream')),
    ]
    response = client.post('/api/laz/upload', files=files)
    assert response.status_code == 200
    data = response.json()
    assert 'files' in data
    assert len(data['files']) == 2

    for name in ['test1', 'test2']:
        input_path = os.path.join('input', 'LAZ', f'{name}.laz')
        output_dir = os.path.join('output', name, 'lidar')
        assert os.path.exists(input_path)
        assert os.path.isdir(output_dir)

    # Cleanup created files/directories
    for name in ['test1', 'test2']:
        try:
            os.remove(os.path.join('input', 'LAZ', f'{name}.laz'))
        except FileNotFoundError:
            pass
        shutil.rmtree(os.path.join('output', name), ignore_errors=True)
