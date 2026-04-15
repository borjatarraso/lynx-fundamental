*** Settings ***
Documentation    API acceptance tests for Lynx FA Python API
Library          Process


*** Variables ***
${PYTHON}        python3


*** Keywords ***
Run Python
    [Arguments]    ${code}
    ${result}=    Run Process    ${PYTHON}    -c    ${code}
    ...    cwd=${CURDIR}/..    timeout=30s    stderr=STDOUT
    RETURN    ${result}


*** Test Cases ***
About API Returns Dict
    ${result}=    Run Python
    ...    from lynx import get_about_text; a=get_about_text(); assert 'author' in a; assert 'license' in a; print('OK')
    Should Contain    ${result.stdout}    OK
    Should Be Equal As Integers    ${result.rc}    0

Tier Classification Works
    ${result}=    Run Python
    ...    from lynx.models import classify_tier, CompanyTier; assert classify_tier(500e9)==CompanyTier.MEGA; assert classify_tier(None)==CompanyTier.NANO; print('OK')
    Should Contain    ${result.stdout}    OK
    Should Be Equal As Integers    ${result.rc}    0

Explanations API Works
    ${result}=    Run Python
    ...    from lynx.metrics.explanations import get_explanation, list_metrics; assert get_explanation('pe_trailing'); assert len(list_metrics())>30; print('OK')
    Should Contain    ${result.stdout}    OK
    Should Be Equal As Integers    ${result.rc}    0

Conclusion API Works
    ${result}=    Run Python
    ...    from lynx.core.conclusion import generate_conclusion; from lynx.models import *; r=AnalysisReport(profile=CompanyProfile(ticker='T',name='T'),valuation=ValuationMetrics(),profitability=ProfitabilityMetrics(),solvency=SolvencyMetrics(),growth=GrowthMetrics(),efficiency=EfficiencyMetrics(),moat=MoatIndicators(),intrinsic_value=IntrinsicValue()); c=generate_conclusion(r); assert c.verdict; print('OK')
    Should Contain    ${result.stdout}    OK
    Should Be Equal As Integers    ${result.rc}    0

ISIN Detection Works
    ${result}=    Run Python
    ...    from lynx.core.ticker import is_isin; assert is_isin('US0378331005'); assert not is_isin('AAPL'); print('OK')
    Should Contain    ${result.stdout}    OK
    Should Be Equal As Integers    ${result.rc}    0

Storage Mode Management
    ${result}=    Run Python
    ...    from lynx.core.storage import set_mode, get_mode, is_testing; set_mode('testing'); assert is_testing(); set_mode('production'); assert not is_testing(); print('OK')
    Should Contain    ${result.stdout}    OK
    Should Be Equal As Integers    ${result.rc}    0

Calculator CAGR Edge Cases
    ${result}=    Run Python
    ...    from lynx.metrics.calculator import _cagr; assert _cagr(100,200,3) is not None; assert _cagr(None,200,3) is None; assert _cagr(0,200,3) is None; assert _cagr(-1,200,3) is None; print('OK')
    Should Contain    ${result.stdout}    OK
    Should Be Equal As Integers    ${result.rc}    0

Export Format Enum
    ${result}=    Run Python
    ...    from lynx.export import ExportFormat; assert ExportFormat.TXT.value=='txt'; assert ExportFormat.HTML.value=='html'; assert ExportFormat.PDF.value=='pdf'; print('OK')
    Should Contain    ${result.stdout}    OK
    Should Be Equal As Integers    ${result.rc}    0
