import streamlit as st

from modules.security.face_authentication import FaceAuthentication


def render_face_lock():
    """Modern login and registration interface for the HCI dashboard."""

    if st.session_state.get("face_authenticated", False):
        return True

    if "auth_page" not in st.session_state:
        st.session_state.auth_page = "login"

    if "auth_notice" not in st.session_state:
        st.session_state.auth_notice = ""

    try:
        auth = FaceAuthentication()
    except Exception as exc:
        st.error(f"Authentication initialization failed: {exc}")
        st.stop()

    # --------------------------------------------------------
    # PAGE DESIGN
    # --------------------------------------------------------

    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1050px;
            padding-top: 3rem;
            padding-bottom: 2rem;
        }

        .auth-hero {
            text-align: center;
            padding: 1.5rem 1rem 1rem 1rem;
        }

        .auth-logo {
            font-size: 3.5rem;
            margin-bottom: 0.2rem;
        }

        .auth-title {
            font-size: 2.5rem;
            font-weight: 750;
            letter-spacing: -1px;
            color: #172554;
            margin: 0;
        }

        .auth-subtitle {
            color: #64748b;
            font-size: 1rem;
            margin-top: 0.6rem;
        }

        .auth-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            padding: 1.6rem;
            margin: 0 auto;
            box-shadow: 0 12px 40px rgba(15, 23, 42, 0.06);
        }

        .auth-card-title {
            font-size: 1.7rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.2rem;
        }

        .auth-card-subtitle {
            color: #64748b;
            font-size: 0.95rem;
            margin-bottom: 1.5rem;
        }

        .auth-footer {
            text-align: center;
            color: #64748b;
            font-size: 0.85rem;
            padding-top: 1.5rem;
        }

        .auth-badge {
            display: inline-block;
            padding: 0.4rem 0.8rem;
            background: #eff6ff;
            color: #1d4ed8;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        div.stButton > button {
            border-radius: 10px;
            min-height: 44px;
            font-weight: 600;
        }

        div[data-testid="stTextInput"] input {
            border-radius: 9px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="auth-hero">
            <div class="auth-logo">🖐️</div>
            <div class="auth-title">Touchless HCI</div>
            <div class="auth-subtitle">
                Your intelligent workspace, secured by face authentication.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # Narrow centered content area.
    left_space, content, right_space = st.columns([1, 1.35, 1])

    with content:

        # ====================================================
        # LOGIN PAGE — DEFAULT PAGE
        # ====================================================

        if st.session_state.auth_page == "login":

            st.markdown(
                """
                <div class="auth-card">
                    <div class="auth-card-title">Welcome back</div>
                    <div class="auth-card-subtitle">
                        Sign in securely using your registered face.
                    </div>
                    <span class="auth-badge">🔒 FACE AUTHENTICATION</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write("")

            if st.session_state.auth_notice:
                st.success(st.session_state.auth_notice)
                st.session_state.auth_notice = ""

            if not auth.is_registered():
                st.info(
                    "You don't have a registered account yet. "
                    "Create one to get started."
                )

            else:
                registered_username = auth.get_registered_username()

                st.text_input(
                    "Registered username",
                    value=registered_username,
                    disabled=True,
                    key="login_username_display",
                )

                st.write("")

                if st.button(
                    "🔓  Login with Face",
                    key="face_login_button",
                    type="primary",
                    use_container_width=True,
                    disabled=not auth.is_registered(),
                ):
                    with st.spinner(
                        "Starting camera verification. "
                        "Keep only one face visible and blink twice, "
                        "or press SPACE to capture."
                    ):
                        result = auth.verify_face()

                    if result.get("authenticated", False):
                        st.session_state.face_authenticated = True
                        st.success("Face verified. Welcome back!")
                        st.rerun()

                    else:
                        st.error(
                            result.get(
                                "message",
                                "Face verification failed. Please try again.",
                            )
                        )

            st.write("")

            st.markdown(
                "<div style='text-align:center;color:#64748b'>"
                "New to Touchless HCI?"
                "</div>",
                unsafe_allow_html=True,
            )

            if st.button(
                "Create an account  →",
                key="go_to_register",
                use_container_width=True,
            ):
                st.session_state.auth_page = "register"
                st.rerun()

        # ====================================================
        # REGISTRATION PAGE
        # ====================================================

        elif st.session_state.auth_page == "register":

            st.markdown(
                """
                <div class="auth-card">
                    <div class="auth-card-title">Create your account</div>
                    <div class="auth-card-subtitle">
                        Register your face to access your touchless workspace.
                    </div>
                    <span class="auth-badge">✨ QUICK REGISTRATION</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write("")

            if auth.is_registered():
                st.warning(
                    "An account is already registered on this installation. "
                    "This prototype supports one registered user at a time. "
                    "Registering a new user will replace the existing face."
                )

                confirm_replace = st.checkbox(
                    "I understand that this will replace the existing registered face.",
                    key="confirm_replace_face",
                )

            else:
                confirm_replace = True

            username = st.text_input(
                "Username",
                placeholder="Choose a username",
                key="new_account_username",
            )

            st.caption(
                "Your face image is stored locally on this computer "
                "for identity verification."
            )

            if st.button(
                "📸  Register with Face",
                key="register_face_button",
                type="primary",
                use_container_width=True,
            ):
                if not username.strip():
                    st.error("Please enter a username.")

                elif not confirm_replace:
                    st.warning(
                        "Please confirm the existing account replacement first."
                    )

                else:
                    with st.spinner(
                        "Opening the camera. Keep only one face visible, then blink twice "
                        "or press SPACE to capture. Press Q to cancel."
                    ):
                        result = auth.register_face(username.strip())

                    if result.get("success", False):
                        st.session_state.auth_page = "login"
                        st.session_state.auth_notice = (
                            "Registration successful! You can now log in "
                            "using your face."
                        )
                        st.rerun()

                    else:
                        st.error(
                            result.get(
                                "message",
                                "Registration failed. Please try again.",
                            )
                        )

            st.write("")

            st.markdown(
                "<div style='text-align:center;color:#64748b'>"
                "Already have an account?"
                "</div>",
                unsafe_allow_html=True,
            )

            if st.button(
                "← Back to Login",
                key="back_to_login",
                use_container_width=True,
            ):
                st.session_state.auth_page = "login"
                st.rerun()

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="auth-footer">
            Multimodal Touchless Human-Computer Interaction Engine<br>
            Face matching alone does not prevent photo or video spoofing.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Do not render the dashboard until authentication succeeds.
    st.stop()

