# Cleanup Checklist

This document outlines optional cleanup tasks after the ADK migration is complete.

---

## ⚠️ Important Notes

- **Legacy code is kept for backward compatibility**
- **Cleanup is optional** - can be done gradually
- **Test thoroughly** before removing any code
- **Consider deprecation period** before removal

---

## Cleanup Tasks

### 1. Code Cleanup

#### Optional: Remove Legacy Agents
- [ ] Remove `agents/research_agent.py` (LangChain version)
- [ ] Remove `agents/technical_agent.py` (LangChain version)
- [ ] Remove `agents/companion_agent.py` (LangChain version)
- [ ] Remove `agents/orchestrator.py` (LangGraph version)
- [ ] Remove `agents/base_agent.py` (if not used elsewhere)

**Note**: Keep if you need backward compatibility or gradual migration.

#### Optional: Remove Legacy Tools
- [ ] Remove `tools/search_tool.py` (Tavily version)
- [ ] Remove `tools/code_exec_tool.py` (if fully replaced)
- [ ] Remove `tools/jd_parser_tool.py` (if fully replaced)

**Note**: Keep if Judge0 is still needed for multi-language support.

#### Optional: Remove Legacy Services
- [ ] Remove `memory/session_service.py` (custom version)
- [ ] Remove `memory/persistent_session_service.py` (custom version)
- [ ] Remove `memory/memory_bank.py` (ChromaDB version)

**Note**: Keep if you need fallback or gradual migration.

### 2. API Cleanup

#### Deprecate Legacy Endpoints
- [ ] Add deprecation warnings to `/api/v1/*` endpoints
- [ ] Update API documentation to mark legacy endpoints as deprecated
- [ ] Add migration notices in API responses
- [ ] Set deprecation date (e.g., 6 months from now)

#### Remove Legacy Endpoints (After Deprecation Period)
- [ ] Remove `/api/v1/research`
- [ ] Remove `/api/v1/technical/*`
- [ ] Remove `/api/v1/sessions` (if replaced)
- [ ] Update API versioning strategy

### 3. Dependencies Cleanup

#### Remove Unused Dependencies
- [ ] Remove `langchain` (if not used)
- [ ] Remove `langchain-community` (if not used)
- [ ] Remove `langgraph` (if not used)
- [ ] Remove `tavily-python` (if not used)
- [ ] Remove `chromadb` (if not used)

**Note**: Check for other usages before removing.

#### Update requirements.txt
- [ ] Remove unused packages
- [ ] Update package versions
- [ ] Add comments for ADK dependencies
- [ ] Document optional dependencies

### 4. Configuration Cleanup

#### Remove Legacy Settings
- [ ] Remove `TAVILY_API_KEY` (if not used)
- [ ] Remove `OPENAI_API_KEY` (if fully migrated to Gemini)
- [ ] Remove `VECTOR_DB_PATH` (if not using ChromaDB)
- [ ] Update `.env.example` to remove legacy variables

#### Update Settings
- [ ] Mark legacy settings as deprecated
- [ ] Add migration notes in settings
- [ ] Update configuration documentation

### 5. Documentation Cleanup

#### Update Documentation
- [ ] Mark legacy documentation as deprecated
- [ ] Update all examples to use ADK
- [ ] Remove outdated guides
- [ ] Archive legacy documentation

#### Create Migration Archive
- [ ] Create `docs/archive/` directory
- [ ] Move legacy documentation to archive
- [ ] Add README in archive explaining migration

### 6. Test Cleanup

#### Remove Legacy Tests
- [ ] Remove `tests/test_agents.py` (if testing only legacy)
- [ ] Remove `tests/test_tools.py` (if testing only legacy)
- [ ] Update test suite to focus on ADK

**Note**: Keep integration tests that verify backward compatibility.

### 7. UI Cleanup

#### Update Streamlit UI
- [ ] Update UI to use ADK endpoints
- [ ] Remove legacy API client code
- [ ] Update error handling for ADK responses
- [ ] Test streaming responses in UI

---

## Recommended Cleanup Timeline

### Phase 1: Immediate (Optional)
- Add deprecation warnings
- Update documentation
- Mark legacy code as deprecated

### Phase 2: Short-term (3-6 months)
- Remove unused dependencies
- Clean up configuration
- Update UI to use ADK

### Phase 3: Long-term (6-12 months)
- Remove legacy endpoints
- Remove legacy code
- Complete migration

---

## Before Removing Code

### Checklist
- [ ] All users migrated to ADK endpoints
- [ ] No dependencies on legacy code
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Deprecation period completed
- [ ] Stakeholder approval

### Testing
- [ ] Run full test suite
- [ ] Test all ADK endpoints
- [ ] Verify backward compatibility (if needed)
- [ ] Test in staging environment

---

## Rollback Plan

If issues arise after cleanup:

1. **Keep Git History**: All code is in Git history
2. **Feature Flags**: Use feature flags to switch between implementations
3. **Gradual Rollout**: Remove code gradually, not all at once
4. **Monitoring**: Monitor for issues after each cleanup step

---

## Notes

- **Conservative Approach**: Keep legacy code longer if unsure
- **User Communication**: Notify users before removing endpoints
- **Version Control**: Tag releases before major cleanup
- **Documentation**: Document all cleanup decisions

---

**Last Updated**: 2025-01-20  
**Status**: Optional - Not Required for Migration Completion

