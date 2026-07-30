# Extension Point Catalog

Auto-generated — Architecture Freeze v10.

---

## Bridge Extensions (82)

Bridge adalah interface conversation ↔ subsystem dan dashboard ↔ subsystem. setiap subsystem punya bridge pair:
- `Conversation{Subsystem}Bridge` — menerima query dari conversation layer
- `Dashboard{Subsystem}Bridge` — menyediakan ExecutionCards ke dashboard

### Bridge Pattern
```
Input (query/DTO) -> Conversation/Dashboard Bridge -> Subsystem processing -> Output (DTO/cards)
```

### Extensibility
Bridges adalah extension point utama. Tambah bridge baru = tambah subsystem baru.

---

## Plugin Extensions (54)

Plugin `src/sam/plugin/` adalah sistem extension formal.

### Registration
- `PluginRegistry` — register by manifest
- `PluginDiscovery` — discover by file/path

### Lifecycle
1. Discover -> 2. Validate -> 3. Load -> 4. Enable -> 5. Execute -> 6. Disable -> 7. Uninstall

### Loading
- `PluginLoader` — dynamic import from plugin directory
- `PluginValidator` — validates manifest against schema

---

## Provider Extensions (53)

Provider adalah interface ke eksternal:
- `TimeProvider` — clock abstraction (SystemClock, VirtualClock, FrozenClock)
- ProviderQueryResult, ProviderCard, ProviderDashboard
- Custom providers via subclass + registration

### Registration
- `ProviderRegistry` — register provider by capability
- Capability-based lookup

---

## Dashboard Extensions (122)

ExecutionCards adalah mekanisme UI extension. Setiap subsystem mendefinisikan:
1. **Layout** — `DashboardLayout`
2. **Widget** — `DashboardWidget`
3. **Cards** — 5-6 ExecutionCards per subsystem (frozen dataclass)

### Registration
- Hardcoded in each `Dashboard*Bridge`
- Cards are immutable (frozen dataclass)

---

## Adapter Extensions (36)

Adapter adalah interface untuk runtime integration:
- `BaseAdapter` — abstract base
- `AdapterRegistry` — register/capability lookup
- `MockAdapter` — testing support

### Registration
- `AdapterRegistry.register(capability, adapter)`
- `AdapterRegistry.lookup(capability) -> adapter`

---

## Launcher Extensions (8)

Launcher adalah entry point eksekusi:
- `HostLauncher` — standalone mode
- `IntegratedLauncher` — embedded mode
- `PluginDiscovery` — launcher-level plugin discovery

### Registration
- `LauncherRegistry` — register by environment type

---

## Runtime Contract Extensions

Runtime Kernel menyediakan:
- `RuntimeLocator` — find runtime by type
- `RuntimeDescriptor` — register runtime with metadata
- `BridgeRouter` — route between bridges
- `TransformEngine` — transform DTOs between subsystems
- `AdapterRegistry` — cross-subsystem adapter lookup
