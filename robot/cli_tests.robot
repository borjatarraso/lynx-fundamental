*** Settings ***
Documentation    CLI acceptance tests for Lynx Fundamental Analysis
Library          Process
Library          OperatingSystem

Suite Setup      Set Testing Mode


*** Variables ***
${PYTHON}        python3


*** Keywords ***
Set Testing Mode
    Set Environment Variable    PYTHONDONTWRITEBYTECODE    1

Run Lynx
    [Arguments]    @{args}
    ${result}=    Run Process    ${PYTHON}    -m    lynx    @{args}
    ...    cwd=${CURDIR}/..    timeout=60s
    ${combined}=    Set Variable    ${result.stdout}\n${result.stderr}
    Set Test Variable    ${OUTPUT}    ${combined}
    RETURN    ${result}

Output Should Contain
    [Arguments]    ${text}
    Should Contain    ${OUTPUT}    ${text}


*** Test Cases ***
Version Flag Shows Version
    ${result}=    Run Lynx    --version
    Output Should Contain    lynx-fundamental
    Output Should Contain    4.0
    Output Should Contain    Lince Investor Suite
    Should Be Equal As Integers    ${result.rc}    0

About Flag Shows Author
    ${result}=    Run Lynx    --about
    Output Should Contain    Borja Tarraso
    Output Should Contain    BSD-3-Clause
    Output Should Contain    borja.tarraso@member.fsf.org
    Should Be Equal As Integers    ${result.rc}    0

Explain Lists All Metrics
    ${result}=    Run Lynx    --explain
    Output Should Contain    pe_trailing
    Output Should Contain    roic
    Output Should Contain    debt_to_equity
    Should Be Equal As Integers    ${result.rc}    0

Explain Specific Metric
    ${result}=    Run Lynx    --explain    pe_trailing
    Output Should Contain    Price-to-Earnings
    Output Should Contain    Formula
    Should Be Equal As Integers    ${result.rc}    0

Explain Unknown Metric Shows Error
    ${result}=    Run Lynx    --explain    nonexistent_metric
    Output Should Contain    Unknown metric
    Should Be Equal As Integers    ${result.rc}    0

Explain Section Lists All Sections
    ${result}=    Run Lynx    --explain-section
    Output Should Contain    valuation
    Output Should Contain    profitability
    Output Should Contain    solvency
    Output Should Contain    growth
    Output Should Contain    moat
    Should Be Equal As Integers    ${result.rc}    0

Explain Specific Section
    ${result}=    Run Lynx    --explain-section    valuation
    Output Should Contain    Valuation Metrics
    Output Should Contain    Price-based ratios
    Should Be Equal As Integers    ${result.rc}    0

Explain Unknown Section Shows Error
    ${result}=    Run Lynx    --explain-section    nonexistent_section
    Output Should Contain    Unknown section
    Should Be Equal As Integers    ${result.rc}    0

Explain Conclusion Overall
    ${result}=    Run Lynx    --explain-conclusion
    Output Should Contain    Conclusion Methodology
    Output Should Contain    weighted average
    Should Be Equal As Integers    ${result.rc}    0

Explain Conclusion Category
    ${result}=    Run Lynx    --explain-conclusion    valuation
    Output Should Contain    Valuation Score
    Should Be Equal As Integers    ${result.rc}    0

Mode Required Without Special Flags
    ${result}=    Run Lynx    AAPL
    Should Not Be Equal As Integers    ${result.rc}    0

Invalid Max Filings Rejected
    ${result}=    Run Lynx    -p    --max-filings    -1    AAPL
    Should Not Be Equal As Integers    ${result.rc}    0

Zero Max Filings Rejected
    ${result}=    Run Lynx    -p    --max-filings    0    AAPL
    Should Not Be Equal As Integers    ${result.rc}    0

List Cache Testing Mode
    ${result}=    Run Lynx    -t    --list-cache
    Should Be Equal As Integers    ${result.rc}    0

Help Flag Works
    ${result}=    Run Lynx    --help
    Output Should Contain    production-mode
    Output Should Contain    testing-mode
    Output Should Contain    --export
    Output Should Contain    --explain
    Output Should Contain    --explain-section
    Output Should Contain    --explain-conclusion
    Output Should Contain    --about
    Should Be Equal As Integers    ${result.rc}    0
