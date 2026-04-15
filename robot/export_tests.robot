*** Settings ***
Documentation    Export acceptance tests for Lynx Fundamental Analysis
Library          Process
Library          OperatingSystem

Suite Setup      Prepare Test Data
Suite Teardown   Cleanup Export Files


*** Variables ***
${PYTHON}        python3
${EXPORT_DIR}    ${CURDIR}/../export_test_output


*** Keywords ***
Prepare Test Data
    Set Environment Variable    PYTHONDONTWRITEBYTECODE    1
    Create Directory    ${EXPORT_DIR}
    # Run a single analysis to populate cache for all export tests
    ${result}=    Run Process    ${PYTHON}    -m    lynx    -t    AAPL    --no-news    --no-reports
    ...    cwd=${CURDIR}/..    timeout=180s
    Should Be Equal As Integers    ${result.rc}    0    msg=Suite setup analysis failed

Cleanup Export Files
    Remove Directory    ${EXPORT_DIR}    recursive=True

Run Export
    [Documentation]    Export using cached analysis via helper script (no network calls).
    [Arguments]    ${fmt}    ${dest}
    ${result}=    Run Process    ${PYTHON}    ${CURDIR}/export_helper.py    AAPL    ${fmt}    ${dest}
    ...    cwd=${CURDIR}/..    timeout=60s
    ${combined}=    Set Variable    ${result.stdout}\n${result.stderr}
    Set Test Variable    ${CLI_OUTPUT}    ${combined}
    RETURN    ${result}


*** Test Cases ***
Export TXT Creates File
    ${txt_path}=    Set Variable    ${EXPORT_DIR}/test_export.txt
    ${result}=    Run Export    txt    ${txt_path}
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain    ${CLI_OUTPUT}    Exported to
    File Should Exist    ${txt_path}
    ${content}=    Get File    ${txt_path}
    Should Contain    ${content}    Apple
    Should Contain    ${content}    Valuation

Export HTML Creates Valid File
    ${html_path}=    Set Variable    ${EXPORT_DIR}/test_export.html
    ${result}=    Run Export    html    ${html_path}
    Should Be Equal As Integers    ${result.rc}    0
    File Should Exist    ${html_path}
    ${content}=    Get File    ${html_path}
    Should Contain    ${content}    <!DOCTYPE html>
    Should Contain    ${content}    Apple
    Should Contain    ${content}    Lynx Fundamental Analysis

Export PDF Shows Error Without Weasyprint
    [Documentation]    PDF export requires weasyprint. If not installed, error message should appear.
    ${pdf_path}=    Set Variable    ${EXPORT_DIR}/test_export.pdf
    ${result}=    Run Export    pdf    ${pdf_path}
    # Either succeeds (weasyprint installed) or fails with helpful message
    Run Keyword If    ${result.rc} != 0
    ...    Should Contain    ${CLI_OUTPUT}    weasyprint
