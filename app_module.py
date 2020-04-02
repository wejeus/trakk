from injector import Module, provider, Injector, inject, singleton
from app import App
from ref_store import RefStore
from linker import Linker
from config import Config
import git

_ERROR_GIT_NOT_INITIALIZED = "Could not initialize git repository"

class AppModule(Module):
    
    @singleton
    @provider
    def provide_config(self) -> Config:
        return Config()

    @singleton
    @provider
    def provide_ref_store(self, config: Config) -> RefStore:
        return RefStore(config)

    @singleton
    @provider
    def provide_git_repo(self, ref_store: RefStore) -> git.Repo:
        repo = git.Repo(ref_store.get_repository())
        assert not repo.bare, _ERROR_GIT_NOT_INITIALIZED
        return repo

    @singleton
    @provider
    def provide_linker(self, ref_store: RefStore) -> Linker:
        return Linker(ref_store.get_repository())

    @singleton
    @provider
    def provide_app(self, config: Config, ref_store: RefStore, linker: Linker, git_repo: git.Repo) -> App:
        return App(config, ref_store, linker, git_repo)
    
    
    

    
         