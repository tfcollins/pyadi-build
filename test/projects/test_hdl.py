import pytest

from adibuild.core.config import BuildConfig
from adibuild.platforms.hdl import HDLPlatform
from adibuild.projects.hdl import HDLBuilder


@pytest.fixture
def hdl_config(tmp_path):
    config_data = {
        "project": "hdl",
        "repository": "https://github.com/analogdevicesinc/hdl.git",
        "tag": "hdl_2023_r2",
        "build": {"output_dir": str(tmp_path / "output")},
        "platforms": {
            "zed_fmcomms2": {
                "name": "zed_fmcomms2",
                "arch": "arm",
                "hdl_project": "fmcomms2",
                "carrier": "zed",
            }
        },
    }
    return BuildConfig(config_data)


def test_hdl_builder_init(hdl_config):
    platform_config = hdl_config.get_platform("zed_fmcomms2")
    platform = HDLPlatform(platform_config)
    builder = HDLBuilder(hdl_config, platform)
    assert builder.config == hdl_config
    assert builder.platform == platform


def test_prepare_source(hdl_config, mocker, tmp_path):
    platform_config = hdl_config.get_platform("zed_fmcomms2")
    platform = HDLPlatform(platform_config)
    builder = HDLBuilder(hdl_config, platform)

    # Mock GitRepository
    mock_repo = mocker.patch("adibuild.projects.hdl.GitRepository")
    mock_repo_instance = mock_repo.return_value
    mock_repo_instance.get_commit_sha.return_value = "12345678"

    # Mock Path.home to redirect cache
    mocker.patch("pathlib.Path.home", return_value=tmp_path)

    # Mock source_dir.exists()
    # We need to mock Path.exists but it's tricky to mock specifically for source_dir
    # Instead we can mock the property or ensure the path exists physically in tmp
    repo_path = tmp_path / ".adibuild" / "repos" / "hdl"
    repo_path.mkdir(parents=True)

    source_dir = builder.prepare_source()

    assert source_dir == repo_path
    mock_repo.assert_called_once()
    mock_repo_instance.ensure_repo.assert_called_with(ref="hdl_2023_r2")


def test_build_execution(hdl_config, mocker, tmp_path):
    platform_config = hdl_config.get_platform("zed_fmcomms2")
    platform = HDLPlatform(platform_config)

    # Enable script mode to avoid real make execution but test flow
    # Or mock executor completely
    builder = HDLBuilder(hdl_config, platform)

    # Mock prepare_source
    mocker.patch.object(builder, "prepare_source")
    builder.source_dir = tmp_path / "hdl"

    # Mock project dir existence
    project_dir = builder.source_dir / "projects" / "fmcomms2" / "zed"
    mocker.patch("pathlib.Path.exists", return_value=True)

    # Mock make
    mock_make = mocker.patch.object(builder.executor, "make")

    # Mock package_artifacts
    mocker.patch.object(builder, "package_artifacts", return_value={"output_dir": "out"})

    builder.build()

    mock_make.assert_called_once()
    # Check that -C project_dir was passed in extra_args
    call_kwargs = mock_make.call_args[1]
    extra_args = call_kwargs.get("extra_args", [])
    assert "-C" in extra_args
    assert str(project_dir) in extra_args


def test_missing_config_fields(tmp_path):
    # Config missing 'carrier'
    config_data = {
        "project": "hdl",
        "platforms": {"bad": {"hdl_project": "fmcomms2", "arch": "arm"}},
    }
    config = BuildConfig(config_data)
    platform = HDLPlatform(config.get_platform("bad"))
    builder = HDLBuilder(config, platform)

    from adibuild.core.executor import BuildError

    with pytest.raises(BuildError, match="requires 'hdl_project' and 'carrier'"):
        builder.build()
