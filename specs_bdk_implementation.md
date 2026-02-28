### BDK (Bitcoin Development Kit)

- **`bdkpython` v2.2.0** — bindings Python disponibles via pip
- **Una misma mnemonic funciona para ambas redes** sin conflicto:
  - Bitcoin: `m/84'/0'/0'` (BDK) — coin_type `0'`
  - Liquid: `m/84'/1776'/0'` (LWK) — coin_type `1776'`
  - SLIP-77 (blinding keys de Liquid) se deriva del mismo seed pero por ruta independiente (SLIP-0021)
- **bdk-cli NO sirve** para integración programática, es solo playground CLI. Usar `bdkpython` directamente.

#### Clases principales de BDK Python

| Clase | Uso |
|-------|-----|
| `Mnemonic` | Generación y parsing de mnemonic BIP39 |
| `DescriptorSecretKey` | Derivar claves desde mnemonic para descriptors |
| `Descriptor` | Output descriptors (BIP84, BIP86, etc.) |
| `Wallet` | Wallet core (descriptors, addresses, UTXOs) |
| `Persister` | Persistencia (in-memory o SQLite) |
| `TxBuilder` | Construcción de transacciones |
| `Psbt` | Partially Signed Bitcoin Transactions |
| `ElectrumClient` / `EsploraClient` | Backends de sync blockchain |
| `Balance` | Balance del wallet |
| `Network` | Enum: BITCOIN, TESTNET, SIGNET, REGTEST |
| `KeychainKind` | EXTERNAL (receive) o INTERNAL (change) |

#### Ejemplo: misma mnemonic, dos redes

```python
# LWK: Liquid wallet
lwk_mnemonic = lwk.Mnemonic(mnemonic)
signer = lwk.Signer(lwk_mnemonic, net)
descriptor = str(signer.wpkh_slip77_descriptor())
# → ct(slip77(...), elwpkh([fp/84h/1776h/0h]xpub/<0;1>/*))

# BDK: Bitcoin wallet (MISMA mnemonic)
from bdkpython import Mnemonic, DescriptorSecretKey, Descriptor, KeychainKind, Network
bdk_mnemonic = Mnemonic.from_string(mnemonic)
secret_key = DescriptorSecretKey(Network.BITCOIN, bdk_mnemonic, None)
btc_descriptor = Descriptor.new_bip84(secret_key, KeychainKind.EXTERNAL, Network.BITCOIN)
# → wpkh([fp/84'/0'/0']xpub/0/*)
```

#### Derivation paths

| Red | Librería | Tipo | Path | Descriptor |
|-----|----------|------|------|------------|
| Bitcoin Mainnet | BDK | BIP84 (SegWit) | `m/84'/0'/0'` | `wpkh([fp/84'/0'/0']xpub/0/*)` |
| Bitcoin Testnet | BDK | BIP84 (SegWit) | `m/84'/1'/0'` | `wpkh([fp/84'/1'/0']tpub/0/*)` |
| Bitcoin Mainnet | BDK | BIP86 (Taproot) | `m/86'/0'/0'` | `tr([fp/86'/0'/0']xpub/0/*)` |
| Liquid Mainnet | LWK | WPKH + SLIP77 | `m/84'/1776'/0'` | `ct(slip77(...), elwpkh([fp/84h/1776h/0h]xpub/<0;1>/*))` |
| Liquid Testnet | LWK | WPKH + SLIP77 | `m/84'/1'/0'` | `ct(slip77(...), elwpkh([fp/84h/1h/0h]tpub/<0;1>/*))` |

---

### EPIC 1: Bitcoin Onchain (BDK)

#### Ticket 1.1 — Módulo `bitcoin.py`: Wallet Bitcoin con BDK

**Descripción**: Crear `src/aqua_mcp/bitcoin.py` con clase `BitcoinWalletManager`.

**Métodos:**
- `create_wallet(mnemonic, network)` — BIP84 descriptor desde la misma mnemonic
- `sync_wallet()` — sync via Esplora (`mempool.space` o `blockstream.info`)
- `get_balance()` → Balance en sats
- `get_address(index)` → dirección `bc1...`
- `get_transactions(limit)` → historial
- `send(address, amount)` → crear PSBT, firmar, broadcast

**Detalles técnicos:**
- Persistencia: reutilizar `storage.py` con tipo `"bitcoin"` en `WalletData`
- Cache SQLite de BDK en `~/.aqua-mcp/cache/<wallet_name>/btc/`
- Electrum servers: `blockstream.info:50002` (mainnet), `blockstream.info:60002` (testnet)

**Dependencia:** `bdkpython>=2.2.0`

---

#### Ticket 1.2 — Herramientas MCP para Bitcoin

**Descripción**: Registrar nuevos tools con prefijo `btc_` en el MCP server.

**Tools:**
- `btc_balance(wallet_name)` — balance Bitcoin
- `btc_address(wallet_name, index)` — generar dirección de recepción
- `btc_transactions(wallet_name, limit)` — historial de transacciones
- `btc_send(wallet_name, address, amount, passphrase)` — enviar BTC

**Implementación:**
- Agregar schemas a `TOOL_SCHEMAS` en `server.py`
- Implementar funciones en `tools.py` siguiendo el patrón existente
- Registrar en dict `TOOLS`

---

#### Ticket 1.3 — Wallet unificada: una mnemonic, dos redes

**Descripción**: Modificar el flujo de import para crear automáticamente wallet en ambas redes.

**Cambios:**
- `lw_import_mnemonic` → renombrar a `import_mnemonic`. esta nueva version al importar, crea wallet Liquid (LWK) + wallet Bitcoin (BDK) con la misma mnemonic
- Nuevo tool `unified_balance(wallet_name)` → muestra balance de ambas redes
- Almacenar descriptor Bitcoin adicional en `WalletData`

---

#### Ticket 1.4 — Tests Bitcoin

**Scope:**
- Unit tests para `BitcoinWalletManager` (mocking BDK)
- Test de integración: misma mnemonic → diferentes direcciones BTC vs Liquid
- Tests de send/receive mockeados
- Test de persistencia SQLite

--
## Fuentes de Investigación

### BDK
- [BDK Python GitHub](https://github.com/bitcoindevkit/bdk-python)
- [BDK Python API Docs](https://bitcoindevkit.github.io/bdk-python/)
- [bdkpython en PyPI](https://pypi.org/project/bdkpython/)
- [Book of BDK - Descriptors](https://bookofbdk.com/cookbook/keys-descriptors/descriptors/)
- [SLIP-0044 Coin Types](https://github.com/satoshilabs/slips/blob/master/slip-0044.md)
- [SLIP-0077 Blinding Keys](https://github.com/satoshilabs/slips/blob/master/slip-0077.md)
