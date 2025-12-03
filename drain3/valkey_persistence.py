# SPDX-License-Identifier: MIT

from typing import Optional, Union

import valkey

from drain3.persistence_handler import PersistenceHandler


class ValkeyPersistence(PersistenceHandler):
    def __init__(self,
                 valkey_host: str,
                 valkey_port: int,
                 valkey_db: int,
                 valkey_pass: Optional[str],
                 is_ssl: bool,
                 valkey_key: Union[bytes, str, memoryview]) -> None:
        self.valkey_host = valkey_host
        self.valkey_port = valkey_port
        self.valkey_db = valkey_db
        self.valkey_pass = valkey_pass
        self.is_ssl = is_ssl
        self.valkey_key = valkey_key
        self.r = valkey.Valkey(host=self.valkey_host,
                             port=self.valkey_port,
                             db=self.valkey_db,
                             password=self.valkey_pass,
                             ssl=self.is_ssl)

    def save_state(self, state: bytes) -> None:
        self.r.set(self.valkey_key, state)

    def load_state(self) -> Optional[bytes]:
        return self.r.get(self.valkey_key)