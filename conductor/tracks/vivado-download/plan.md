# Track: Robust Vivado Download Strategy

## Status
- [x] Phase 1: Fix regressions in unit tests - COMPLETE
- [x] Phase 2: Refine Selenium and Playwright strategies - COMPLETE
- [~] Phase 3: Verify with integration tests - ATTEMPTED

## Phases

### Phase 1: Fix regressions in unit tests
- [x] [x] Fix `test_generate_script_zynqmp` in `test/cli/test_script_generation.py`
- [x] [x] Fix `test_auth_bootstrap_url_normalizes_legacy_xilinx_downloads` in `test/core/test_vivado_installer.py`
- [x] [x] Fix `test_playwright_download_bootstraps_login_before_authenticated_http` in `test/core/test_vivado_installer.py`
- [x] [x] Fix `test_microblaze_kernel_target_warning` in `test/linux/test_microblaze_platform.py`
- [x] [x] Fix `test_cmake_real_execution_changes_cwd` in `test/projects/test_libad9361.py`

### Phase 2: Refine Selenium and Playwright strategies
- [x] [x] Verify `SeleniumDownloadStrategy` against PoC
- [x] [x] Ensure `PlaywrightDownloadStrategy` handles mocks correctly in tests
- [x] [x] Consolidate common browser automation helpers (Updated bootstrap URLs and added stealth)

### Phase 3: Verify with integration tests
- [~] [ ] Run `test/integration/test_amd_account_access.py` (Encountered timeouts on account.amd.com)
- [ ] [ ] Verify full download flow (Requires credentials)
