# Open Source Credits and Licenses

This project, **CreditCampus**, utilizes several open-source packages and libraries. We would like to thank the creators and maintainers of these projects.

Below is a list of the open-source software packages used in this project along with their respective licenses.

## Python Packages (Backend)

| Package | Version | License | Homepage / Repository |
| :--- | :--- | :--- | :--- |
| **Django** | `>=5.0, <6.0` | BSD-3-Clause | [djangoproject.com](https://www.djangoproject.com/) |
| **gunicorn** | `>=21.2.0` | MIT | [gunicorn.org](https://gunicorn.org/) |
| **psycopg2-binary** | `>=2.9.9` | LGPL-3.0-or-later with exceptions | [psycopg.org](https://www.psycopg.org/) |
| **python-dotenv** | `>=1.0.1` | BSD-3-Clause | [github.com/theskumar/python-dotenv](https://github.com/theskumar/python-dotenv) |
| **google-genai** | `>=0.1.1` | Apache-2.0 | [github.com/google/generative-ai-python](https://github.com/google/generative-ai-python) |
| **channels** | `>=4.0.0` | BSD-3-Clause | [github.com/django/channels](https://github.com/django/channels) |
| **channels-redis** | `>=4.0.0` | BSD-3-Clause | [github.com/django/channels_redis](https://github.com/django/channels_redis) |
| **daphne** | `>=4.0.0` | BSD-3-Clause | [github.com/django/daphne](https://github.com/django/daphne) |

## Frontend Libraries (CDNs & Fonts)

| Library / Resource | License | Homepage / Repository | Description |
| :--- | :--- | :--- | :--- |
| **Tailwind CSS** (via Play CDN) | MIT | [tailwindcss.com](https://tailwindcss.com/) | Utility-first CSS framework |
| **Remix Icon** | Apache-2.0 (Icons) / SIL OFL 1.1 (Font) | [remixicon.com](https://remixicon.com/) | Open-source neutral style icon system |
| **Outfit Font** | SIL Open Font License 1.1 | [fonts.google.com/specimen/Outfit](https://fonts.google.com/specimen/Outfit) | Sans-serif geometric typeface |
| **Inter Font** | SIL Open Font License 1.1 | [fonts.google.com/specimen/Inter](https://fonts.google.com/specimen/Inter) | Typeface specially designed for user interfaces |

---

## Detailed License Information

### BSD-3-Clause License
*Applied to Django, python-dotenv, channels, channels-redis, daphne*

```
Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

### MIT License
*Applied to gunicorn, Tailwind CSS*

```
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

### Apache License 2.0
*Applied to google-genai, Remix Icon*

```
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

### LGPL-3.0 (GNU Lesser General Public License v3.0)
*Applied to psycopg2-binary (with OpenSSL linkage exception)*

```
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

### SIL Open Font License 1.1
*Applied to Outfit Font, Inter Font, Remix Icon font files*

```
This Font Software is licensed under the SIL Open Font License, Version 1.1.
This license is available with a FAQ at: http://scripts.sil.org/OFL
```
