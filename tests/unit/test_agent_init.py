from app.agent import root_agent
from app.agents import (
    adr_architect_agent,
    branch_doc_writer_agent,
    gitops_remediation_agent,
    polyglot_auditor_agent,
    regulatory_rag_agent,
)


def test_root_agent_initialization():
    assert root_agent.name == "audit_orchestrator"
    assert len(root_agent.sub_agents) == 5

    sub_agent_names = [sa.name for sa in root_agent.sub_agents]
    assert "polyglot_code_iac_auditor" in sub_agent_names
    assert "regulatory_rag_agent" in sub_agent_names
    assert "adr_architect_agent" in sub_agent_names
    assert "branch_doc_writer_agent" in sub_agent_names
    assert "gitops_remediation_agent" in sub_agent_names


def test_sub_agents_configuration():
    assert polyglot_auditor_agent.name == "polyglot_code_iac_auditor"
    assert len(polyglot_auditor_agent.tools) == 2

    assert regulatory_rag_agent.name == "regulatory_rag_agent"
    assert len(regulatory_rag_agent.tools) == 1

    assert adr_architect_agent.name == "adr_architect_agent"
    assert len(adr_architect_agent.tools) == 1

    assert branch_doc_writer_agent.name == "branch_doc_writer_agent"

    assert gitops_remediation_agent.name == "gitops_remediation_agent"
    assert len(gitops_remediation_agent.tools) == 1
