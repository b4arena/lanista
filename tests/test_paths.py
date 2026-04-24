from lanista import paths


def test_xdg_config_home_override(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    assert paths.config_dir() == tmp_path / "cfg" / "lanista"
    assert paths.aliases_path() == tmp_path / "cfg" / "lanista" / "aliases.json"
    assert paths.sources_config_dir() == tmp_path / "cfg" / "lanista" / "sources"


def test_xdg_cache_home_override(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    assert paths.cache_dir() == tmp_path / "cache" / "lanista"
    assert paths.index_path() == tmp_path / "cache" / "lanista" / "model_index.json"
    assert paths.sources_cache_dir() == tmp_path / "cache" / "lanista" / "sources"


def test_source_path_curated_vs_fetched(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    assert paths.source_path("gkisokay", curated=True) == (
        tmp_path / "cfg" / "lanista" / "sources" / "gkisokay.json"
    )
    assert paths.source_path("openrouter", curated=False) == (
        tmp_path / "cache" / "lanista" / "sources" / "openrouter.json"
    )


def test_defaults_without_env(monkeypatch, tmp_path):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert paths.config_dir() == tmp_path / ".config" / "lanista"
    assert paths.cache_dir() == tmp_path / ".cache" / "lanista"
