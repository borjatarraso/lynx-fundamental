*** Settings ***
Documentation    Export acceptance tests for Lynx Fundamental Analysis
Library          Process
Library          OperatingSystem

Suite Setup      Set Testing Mode
Suite Teardown   Cleanup Export Files


*** Variables ***
${PYTHON}        python3
${EXPORT_DIR}    ${CURDIR}/../export_test_output


*** Keywords ***
Set Testing Mode
    Set Environment Variable    PYTHONDONTWRITEBYTECODE    1
    Create Directory    ${EXPORT_DIR}

Cleanup Export Files
    Remove Directory    ${EXPORT_DIR}    recursive=True

Run Lynx
    [Arguments]    @{args}
    ${result}=    Run Process    ${PYTHON}    -m    lynx    @{args}
    ...    cwd=${CURDIR}/..    timeout=120s
    ${combined}=    Set Variable    ${result.stdout}\n${result.stderr}
    Set Test Variable    ${OUTPUT}    ${combined}
    RETURN    ${result}


*** Test Cases ***
Export TXT Creates File
    ${output}=    Set Variable    ${EXPORT_DIR}/test_export.txt
    ${result}=    Run Lynx    -t    AAPL    --export    txt    --output    ${output}    --no-news
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain    ${OUTPUT}    Exported to
    File Should Exist    ${output}
    ${content}=    Get File    ${output}
    Should Contain    ${content}    Apple
    Should Contain    ${content}    Valuation

Export HTML Creates Valid File
    ${output}=    Set Variable    ${EXPORT_DIR}/test_export.html
    ${result}=    Run Lynx    -t    AAPL    --export    html    --output    ${output}    --no-news
    Should Be Equal As Integers    ${result.rc}    0
    File Should Exist    ${output}
    ${content}=    Get File    ${output}
    Should Contain    ${content}    <!DOCTYPE html>
    Should Contain    ${content}    Apple
    Should Contain    ${content}    Lynx FA

Export PDF Shows Error Without Weasyprint
    [Documentation]    PDF export requires weasyprint. If not installed, error message should appear.
    ${output}=    Set Variable    ${EXPORT_DIR}/test_export.pdf
    ${result}=    Run Lynx    -t    AAPL    --export    pdf    --output    ${output}    --no-news
    # Either succeeds (weasyprint installed) or fails with helpful message
    Run Keyword If    ${result.rc} != 0
    ...    Should Contain    ${OUTPUT}    weasyprint
