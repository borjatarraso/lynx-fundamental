"""Lynx Fundamental Analysis — Value investing research tool with moat analysis."""

__version__ = "2.0"
__author__ = "Borja Tarraso"
__author_email__ = "borja.tarraso@member.fsf.org"
__year__ = "2026"
__license__ = "BSD-3-Clause"

LICENSE_TEXT = """\
BSD 3-Clause License

Copyright (c) 2026, Borja Tarraso <borja.tarraso@member.fsf.org>

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE."""


def get_logo_ascii() -> str:
    """Load ASCII logo from img/logo_ascii.txt."""
    import os
    logo_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "img", "logo_ascii.txt",
    )
    try:
        with open(logo_path, "r") as f:
            return f.read().rstrip("\n")
    except OSError:
        return ""


def get_about_text() -> dict:
    """Return structured about information."""
    return {
        "name": "Lynx Fundamental Analysis",
        "suite": "Lince Investor Suite",
        "version": __version__,
        "author": __author__,
        "email": __author_email__,
        "year": __year__,
        "license": __license__,
        "license_text": LICENSE_TEXT,
        "description": (
            "Value investing research tool with moat analysis. "
            "Fetches, calculates, and displays 40+ financial metrics, "
            "SEC filings, and news for any publicly traded company.\n\n"
            "Part of the Lince Investor Suite."
        ),
    }
