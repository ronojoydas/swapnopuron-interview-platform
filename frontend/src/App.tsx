
import { useEffect, useState, type FormEvent } from "react";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const TOKEN_KEY = "access_token";

type User = {
  id: number;
  full_name: string;
  email: string;
  role: string;
};

type Opportunity = {
  id: number;
  title: string;
  description: string;
  opportunity_type: string;
  location: string | null;
  status: string;
};


type Application = {
  id: number;
  candidate_id: number;
  opportunity_id: number;
  status: string;
  applied_at: string;
  candidate_name?: string | null;
  candidate_email?: string | null;
  candidate_phone?: string | null;
  candidate_education?: string | null;
  candidate_skills?: string | null;
  candidate_experience?: string | null;
};


type Interview = {
  id: number;
  application_id: number;
  interviewer_id: number;
  scheduled_at: string;
  status: string;
  meeting_link: string | null;

};

type Interviewer = {
  id: number;
  full_name: string;
  email: string;
};

type Feedback = {
  id: number;
  interview_id: number;
  interviewer_id: number;
  technical_score: number;
  communication_score: number;
  problem_solving_score: number;
  comments: string;
  recommendation: string;
};

type CandidateProfile = {
  phone: string | null;
  education: string | null;
  skills: string | null;
  experience: string | null;
  resume_path: string | null;
};

type OpportunityForm = {
  title: string;
  description: string;
  opportunity_type: string;
  location: string;
};

type RegistrationForm = {
  full_name: string;
  email: string;
  password: string;
};

const APPLICATION_STATUSES = ["applied", "screening", "shortlisted", "interview", "selected", "rejected"];

const EMPTY_PROFILE: CandidateProfile = {
  phone: "",
  education: "",
  skills: "",
  experience: "",
  resume_path: "",
};

const EMPTY_OPPORTUNITY: OpportunityForm = {
  title: "",
  description: "",
  opportunity_type: "Volunteer",
  location: "Sundarbans, West Bengal",
};

const roleLabels: Record<string, string> = {
  admin: "Administrator",
  staff: "Recruitment Staff",
  interviewer: "Interviewer",
  candidate: "Candidate",
};

async function apiRequest(
  path: string,
  token: string,
  options: RequestInit = {},
) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (response.status === 401) {
    sessionStorage.removeItem(TOKEN_KEY);
    throw new Error("Your session has expired. Please sign in again.");
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : `Request failed (${response.status}).`,
    );
  }

  return data;
}

function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState(
    () => sessionStorage.getItem(TOKEN_KEY) || "",
  );

  const [isRegistering, setIsRegistering] = useState(false);
  const [registration, setRegistration] = useState<RegistrationForm>({
    full_name: "",
    email: "",
    password: "",
  });
  const [registrationLoading, setRegistrationLoading] = useState(false);
  const [registrationError, setRegistrationError] = useState("");
  const [registrationSuccess, setRegistrationSuccess] = useState("");

  const [page, setPage] = useState<"overview" | "opportunities" | "profile" | "my-applications" | "applications" | "interviews" | "feedback">("overview");

  const [profile, setProfile] = useState<CandidateProfile>({ ...EMPTY_PROFILE });
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileError, setProfileError] = useState("");
  const [profileMessage, setProfileMessage] = useState("");
  const [myApplications, setMyApplications] = useState<Application[]>([]);
  const [allApplications, setAllApplications] = useState<Application[]>([]);
  const [applicationSearch, setApplicationSearch] = useState("");
  const [applicationStatusFilter, setApplicationStatusFilter] = useState("all");
  const [applicationOpportunityFilter, setApplicationOpportunityFilter] = useState("all");
  const [applicationsLoading, setApplicationsLoading] = useState(false);
  const [applicationsError, setApplicationsError] = useState("");
  const [applyingOpportunityId, setApplyingOpportunityId] = useState<number | null>(null);
  const [applicationMessage, setApplicationMessage] = useState("");
  const [applicationUpdatingId, setApplicationUpdatingId] = useState<number | null>(null);


  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [interviewers, setInterviewers] = useState<Interviewer[]>([]);
  const [schedulingApplicationId, setSchedulingApplicationId] = useState<number | null>(null);
  const [interviewsLoading, setInterviewsLoading] = useState(false);
  const [interviewsError, setInterviewsError] = useState("");
  const [interviewMessage, setInterviewMessage] = useState("");
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const [schedulingInterview, setSchedulingInterview] = useState(false);
  const [interviewUpdatingId, setInterviewUpdatingId] = useState<number | null>(null);
  const [reschedulingInterviewId, setReschedulingInterviewId] = useState<number | null>(null);
  const [rescheduleDateTime, setRescheduleDateTime] = useState("");
  const [rescheduleInterviewerId, setRescheduleInterviewerId] = useState("");
  const [rescheduleMeetingLink, setRescheduleMeetingLink] = useState("");
  const [rescheduleLoading, setRescheduleLoading] = useState(false);
  const [rescheduleError, setRescheduleError] = useState("");
  const [newInterview, setNewInterview] = useState({
    application_id: "",
    interviewer_id: "",
    scheduled_at: "",
    meeting_link: "",
  });
  const [feedbackByInterview, setFeedbackByInterview] = useState<Record<number, Feedback>>({});
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [feedbackError, setFeedbackError] = useState("");
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [feedbackSubmittingId, setFeedbackSubmittingId] = useState<number | null>(null);
  const [feedbackFormByInterview, setFeedbackFormByInterview] = useState<Record<number, {
    technical_score: string;
    communication_score: string;
    problem_solving_score: string;
    comments: string;
    recommendation: string;
  }>>({});


  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [opportunitiesLoading, setOpportunitiesLoading] = useState(false);
  const [opportunitiesError, setOpportunitiesError] = useState("");

  const [dashboardOpportunities, setDashboardOpportunities] = useState<Opportunity[]>([]);
  const [dashboardApplications, setDashboardApplications] = useState<Application[]>([]);
  const [dashboardInterviews, setDashboardInterviews] = useState<Interview[]>([]);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [dashboardError, setDashboardError] = useState("");
  const [dashboardRefresh, setDashboardRefresh] = useState(0);


  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState("");
  const [createSuccess, setCreateSuccess] = useState("");
  const [newOpportunity, setNewOpportunity] =
    useState<OpportunityForm>({ ...EMPTY_OPPORTUNITY });

  const [closingOpportunityId, setClosingOpportunityId] =
    useState<number | null>(null);
  const [closeError, setCloseError] = useState("");

  // Restore and validate the existing session.
  useEffect(() => {
    if (!token) {
      setUser(null);
      return;
    }

    let cancelled = false;

    apiRequest("/auth/me", token)
      .then((profile: User) => {
        if (!cancelled) setUser(profile);
      })
      .catch((err: Error) => {
        if (!cancelled) {
          sessionStorage.removeItem(TOKEN_KEY);
          setToken("");
          setUser(null);
          setError(err.message);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  // Load live metrics whenever the Overview dashboard is opened.
  useEffect(() => {
    if (!user || page !== "overview") return;

    let cancelled = false;
    setDashboardLoading(true);
    setDashboardError("");

    const loadDashboard = async () => {
      try {
        const opportunityPromise = apiRequest("/opportunities", token) as Promise<Opportunity[]>;
        const applicationPromise = (user.role === "candidate" || user.role === "admin" || user.role === "staff")
          ? apiRequest(user.role === "candidate" ? "/applications/me" : "/applications", token) as Promise<Application[]>
          : Promise.resolve([] as Application[]);
        const interviewPromise = apiRequest("/interviews", token) as Promise<Interview[]>;

        const [opportunityData, applicationData, interviewData] = await Promise.all([
          opportunityPromise,
          applicationPromise,
          interviewPromise,
        ]);

        if (!cancelled) {
          setDashboardOpportunities(opportunityData);
          setDashboardApplications(applicationData);
          setDashboardInterviews(interviewData);
        }
      } catch (err) {
        if (!cancelled) {
          setDashboardError(
            err instanceof Error ? err.message : "Could not load dashboard metrics.",
          );
        }
      } finally {
        if (!cancelled) setDashboardLoading(false);
      }
    };

    loadDashboard();
    return () => {
      cancelled = true;
    };
  }, [user, page, token, dashboardRefresh]);

  // Load opportunities when the Opportunities page is opened.
  useEffect(() => {
    if (!user || page !== "opportunities") return;

    let cancelled = false;

    setOpportunitiesLoading(true);
    setOpportunitiesError("");

    apiRequest("/opportunities", token)
      .then((data: Opportunity[]) => {
        if (!cancelled) setOpportunities(data);
      })
      .catch((err: Error) => {
        if (!cancelled) setOpportunitiesError(err.message);
      })
      .finally(() => {
        if (!cancelled) setOpportunitiesLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [user, page, token]);

  useEffect(() => {
    if (!user || user.role !== "candidate" || page !== "opportunities") return;
    let cancelled = false;
    apiRequest("/applications/me", token)
      .then((data: Application[]) => { if (!cancelled) setMyApplications(data); })
      .catch(() => { /* Applying will show the API's actionable error if needed. */ });
    return () => { cancelled = true; };
  }, [user, page, token]);

  
  useEffect(() => {
    if (!user || page !== "profile" || user.role !== "candidate") return;

    let cancelled = false;
    setProfileLoading(true);
    setProfileError("");
    setProfileMessage("");

    apiRequest("/candidates/me", token)
      .then((data: CandidateProfile) => {
        if (cancelled) return;

        setProfile({
          phone: data.phone ?? "",
          education: data.education ?? "",
          skills: data.skills ?? "",
          experience: data.experience ?? "",
          resume_path: data.resume_path ?? "",
        });
      })
      .catch((err: Error) => {
        if (cancelled) return;

        if (err.message === "Candidate profile not found") {
          setProfile({ ...EMPTY_PROFILE });
          setProfileError("");
        } else {
          setProfileError(err.message);
        }
      })
      .finally(() => {
        if (!cancelled) setProfileLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [user, page, token]);


  useEffect(() => {
    if (!user || page !== "interviews") return;
    let cancelled = false;
    setInterviewsLoading(true);
    setInterviewsError("");
    apiRequest("/interviews", token)
      .then((data: Interview[]) => { if (!cancelled) setInterviews(data); })
      .catch((err: Error) => { if (!cancelled) setInterviewsError(err.message); })
      .finally(() => { if (!cancelled) setInterviewsLoading(false); });
    return () => { cancelled = true; };
  }, [user, page, token]);

  useEffect(() => {
    if (!user || page !== "feedback") return;
    let cancelled = false;
    setFeedbackLoading(true);
    setFeedbackError("");
    apiRequest("/interviews", token)
      .then(async (data: Interview[]) => {
        const completed = data.filter((item) => item.status === "completed");
        if (!cancelled) setInterviews(data);
        const results = await Promise.all(completed.map(async (item) => {
          try {
            const feedback: Feedback = await apiRequest(`/feedback/${item.id}`, token);
            return [item.id, feedback] as const;
          } catch (err) {
            // A 404 means no feedback has been submitted for this completed interview yet.
            if (err instanceof Error && /not found|404/i.test(err.message)) return null;
            return null;
          }
        }));
        if (!cancelled) {
          const existing: Record<number, Feedback> = {};
          results.forEach((entry) => { if (entry) existing[entry[0]] = entry[1]; });
          setFeedbackByInterview(existing);
        }
      })
      .catch((err: Error) => { if (!cancelled) setFeedbackError(err.message); })
      .finally(() => { if (!cancelled) setFeedbackLoading(false); });
    return () => { cancelled = true; };
  }, [user, page, token]);

  useEffect(() => {
    if (!user || (page !== "my-applications" && page !== "applications")) return;
    let cancelled = false;
    setApplicationsLoading(true); setApplicationsError(""); setApplicationMessage("");
    const endpoint = user.role === "candidate" ? "/applications/me" : "/applications";
    apiRequest(endpoint, token)
      .then((data: Application[]) => { if (!cancelled) { if (user.role === "candidate") setMyApplications(data); else setAllApplications(data); } })
      .catch((err: Error) => { if (!cancelled) setApplicationsError(err.message); })
      .finally(() => { if (!cancelled) setApplicationsLoading(false); });
    return () => { cancelled = true; };
  }, [user, page, token]);

  
  async function handleSaveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setProfileError("");
    setProfileMessage("");
    setProfileSaving(true);

    try {
      let method: "POST" | "PUT" = "PUT";

      try {
        await apiRequest("/candidates/me", token);
      } catch (err) {
        if (
          err instanceof Error &&
          err.message === "Candidate profile not found"
        ) {
          method = "POST";
        } else {
          throw err;
        }
      }

      await apiRequest("/candidates/me", token, {
        method,
        body: JSON.stringify(profile),
      });

      setProfileMessage("Profile saved successfully.");
    } catch (err) {
      setProfileError(
        err instanceof Error ? err.message : "Could not save profile.",
      );
    } finally {
      setProfileSaving(false);
    }
  }


  async function handleApply(opportunity: Opportunity) {
    setApplicationMessage(""); setApplyingOpportunityId(opportunity.id);
    try {
      await apiRequest(`/applications/${opportunity.id}`, token, { method: "POST" });
      setApplicationMessage(`Successfully applied for ${opportunity.title}.`);
      const updated: Application[] = await apiRequest("/applications/me", token);
      setMyApplications(updated);
    } catch (err) { setApplicationMessage(err instanceof Error ? err.message : "Could not submit application."); }
    finally { setApplyingOpportunityId(null); }
  }

  async function handleApplicationStatus(applicationId: number, status: string) {
    setApplicationsError(""); setApplicationMessage(""); setApplicationUpdatingId(applicationId);
    try {
      await apiRequest(`/applications/${applicationId}/status`, token, { method: "PATCH", body: JSON.stringify({ status }) });
      setAllApplications((current) => current.map((item) => item.id === applicationId ? { ...item, status } : item));
      setApplicationMessage(`Application #${applicationId} updated to ${status}.`);
    } catch (err) { setApplicationsError(err instanceof Error ? err.message : "Could not update application."); }
    finally { setApplicationUpdatingId(null); }
  }

  async function loadInterviewers() {
  try {
    const data: Interviewer[] = await apiRequest(
      "/interviews/interviewers",
      token,
    );
    setInterviewers(data);
  } catch (err) {
    setInterviewsError(
      err instanceof Error ? err.message : "Could not load interviewers.",
    );
  }
}

  async function handleScheduleInterview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setInterviewsError("");
    setInterviewMessage("");
    setSchedulingInterview(true);
    try {
      // datetime-local has no timezone. Attach the backend-required India offset.
      const scheduledAt = `${newInterview.scheduled_at}:00+05:30`;
      await apiRequest("/interviews", token, {
        method: "POST",
        body: JSON.stringify({
          application_id: Number(newInterview.application_id),
          interviewer_id: Number(newInterview.interviewer_id),
          scheduled_at: scheduledAt,
          meeting_link: newInterview.meeting_link.trim() || null,
        }),
      });
      const updated: Interview[] = await apiRequest("/interviews", token);
      setInterviews(updated);
      setNewInterview({ application_id: "", interviewer_id: "", scheduled_at: "", meeting_link: "" });
      setShowScheduleForm(false);
      setSchedulingApplicationId(null);
      setInterviewMessage("Interview scheduled successfully.");
    } catch (err) {
      setInterviewsError(err instanceof Error ? err.message : "Could not schedule interview.");
    } finally {
      setSchedulingInterview(false);
    }
  }

  async function handleInterviewStatus(interviewId: number, status: "completed" | "cancelled") {
    if (status === "cancelled") {
  const confirmed = window.confirm(
    `Are you sure you want to cancel interview #${interviewId}?`
  );

  if (!confirmed) {
    return;
  }
}
    setInterviewsError("");
    setInterviewMessage("");
    setInterviewUpdatingId(interviewId);
    try {
      const updatedInterview: Interview = await apiRequest(
        `/interviews/${interviewId}/status?status_value=${status}`,
        token,
        { method: "PATCH" },
      );
      setInterviews((current) => current.map((item) => item.id === interviewId ? updatedInterview : item));
      setInterviewMessage(`Interview #${interviewId} marked ${status}.`);
    } catch (err) {
      setInterviewsError(err instanceof Error ? err.message : "Could not update interview status.");
    } finally {
      setInterviewUpdatingId(null);
    }
  }

async function handleRescheduleInterview(
  event: FormEvent<HTMLFormElement>,
  interviewId: number,
) {
  event.preventDefault();
  setRescheduleError("");
  setRescheduleLoading(true);

  try {
    if (!rescheduleDateTime || !rescheduleInterviewerId) {
      throw new Error("Select an interviewer and date/time.");
    }

    // Interpret the datetime-local value as India time.
    const scheduledAt = `${rescheduleDateTime}:00+05:30`;

    const updated: Interview = await apiRequest(
      `/interviews/${interviewId}`,
      token,
      {
        method: "PATCH",
        body: JSON.stringify({
          interviewer_id: Number(rescheduleInterviewerId),
          scheduled_at: scheduledAt,
          meeting_link: rescheduleMeetingLink.trim() || null,
        }),
      },
    );

    const refreshed: Interview[] = await apiRequest("/interviews", token);
    setInterviews(refreshed);
    setReschedulingInterviewId(null);
    setRescheduleDateTime("");
    setRescheduleInterviewerId("");
    setRescheduleMeetingLink("");
    setInterviewMessage(`Interview #${updated.id} rescheduled successfully.`);
  } catch (err) {
    setRescheduleError(
      err instanceof Error ? err.message : "Could not reschedule interview.",
    );
  } finally {
    setRescheduleLoading(false);
  }
}

  async function handleSubmitFeedback(event: FormEvent<HTMLFormElement>, interviewId: number) {
    event.preventDefault();
    setFeedbackError("");
    setFeedbackMessage("");

const form = feedbackFormByInterview[interviewId];

if (!form) {
  setFeedbackError("Please complete the feedback form.");
  return;
}

const scores = [
  Number(form.technical_score),
  Number(form.communication_score),
  Number(form.problem_solving_score),
];

if (
  scores.some(
    (score) => !Number.isInteger(score) || score < 1 || score > 5
  )
) {
  setFeedbackError("All scores must be whole numbers between 1 and 5.");
  return;
}

if (!form.comments.trim()) {
  setFeedbackError("Please enter interview comments.");
  return;
}

    setFeedbackSubmittingId(interviewId);
    try {
      const feedback: Feedback = await apiRequest(`/feedback/${interviewId}`, token, {
        method: "POST",
        body: JSON.stringify({
          technical_score: Number(form.technical_score),
          communication_score: Number(form.communication_score),
          problem_solving_score: Number(form.problem_solving_score),
          comments: form.comments.trim(),
          recommendation: form.recommendation,
        }),
      });
      setFeedbackByInterview((current) => ({ ...current, [interviewId]: feedback }));
      setFeedbackMessage(`Feedback submitted for interview #${interviewId}.`);
    } catch (err) {
      setFeedbackError(err instanceof Error ? err.message : "Could not submit feedback.");
    } finally {
      setFeedbackSubmittingId(null);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Login failed. Check your credentials.",
        );
      }

      if (
        typeof data.access_token !== "string" ||
        !data.access_token
      ) {
        throw new Error("The server did not return an access token.");
      }

      sessionStorage.setItem(TOKEN_KEY, data.access_token);
      setToken(data.access_token);
      setPassword("");
    } catch (err) {
      setError(
        err instanceof TypeError
          ? "Cannot reach the server. Check that FastAPI is running."
          : err instanceof Error
            ? err.message
            : "Something went wrong. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setRegistrationError("");
    setRegistrationSuccess("");
    setRegistrationLoading(true);

    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: registration.full_name.trim(),
          email: registration.email.trim(),
          password: registration.password,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : `Registration failed (${response.status}).`,
        );
      }

      setEmail(registration.email.trim());
      setPassword("");
      setRegistration({
        full_name: "",
        email: "",
        password: "",
      });
      setIsRegistering(false);
      setRegistrationSuccess(
        "Account created successfully! Sign in with your new credentials.",
      );
      setError("");
    } catch (err) {
      setRegistrationError(
        err instanceof TypeError
          ? "Cannot reach the server. Check that FastAPI is running."
          : err instanceof Error
            ? err.message
            : "Registration failed. Please try again.",
      );
    } finally {
      setRegistrationLoading(false);
    }
  }

  function handleLogout() {
    sessionStorage.removeItem(TOKEN_KEY);
    setToken("");
    setUser(null);
    setEmail("");
    setPassword("");
    setError("");
    setPage("overview");
    setProfile({ ...EMPTY_PROFILE });
    setMyApplications([]);
    setAllApplications([]);
    setOpportunities([]);
    setOpportunitiesError("");
    setShowCreateForm(false);
    setCreateError("");
    setCreateSuccess("");
    setCloseError("");
    setClosingOpportunityId(null);
  }

  async function handleCreateOpportunity(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setCreateError("");
    setCreateSuccess("");
    setCloseError("");
    setCreateLoading(true);

    try {
      await apiRequest("/opportunities", token, {
        method: "POST",
        body: JSON.stringify({
          title: newOpportunity.title.trim(),
          description: newOpportunity.description.trim(),
          opportunity_type: newOpportunity.opportunity_type,
          location: newOpportunity.location.trim() || null,
        }),
      });

      const updated: Opportunity[] = await apiRequest(
        "/opportunities",
        token,
      );

      setOpportunities(updated);
      setNewOpportunity({ ...EMPTY_OPPORTUNITY });
      setShowCreateForm(false);
      setCreateSuccess("Opportunity created successfully.");
    } catch (err) {
      setCreateError(
        err instanceof Error
          ? err.message
          : "Could not create the opportunity.",
      );
    } finally {
      setCreateLoading(false);
    }
  }

  async function handleCloseOpportunity(opportunity: Opportunity) {
    const confirmed = window.confirm(
      `Are you sure you want to close "${opportunity.title}"?`,
    );

    if (!confirmed) return;

    setCloseError("");
    setCreateError("");
    setCreateSuccess("");
    setClosingOpportunityId(opportunity.id);

    try {
      await apiRequest(
        `/opportunities/${opportunity.id}/close`,
        token,
        { method: "PATCH" },
      );

      const updated: Opportunity[] = await apiRequest(
        "/opportunities",
        token,
      );

      setOpportunities(updated);
      setCreateSuccess(
        `"${opportunity.title}" has been closed successfully.`,
      );
    } catch (err) {
      setCloseError(
        err instanceof Error
          ? err.message
          : "Could not close the opportunity.",
      );
    } finally {
      setClosingOpportunityId(null);
    }
  }

  // Login and registration screens.
  if (!user) {
    return (
      <main className="login-page">
        <section className="login-panel">
          <div className="brand">
            <div className="brand-mark">S</div>
            <div>
              <h1>Swapnopuron</h1>
              <p>RECRUITMENT &amp; PEOPLE</p>
            </div>
          </div>

          <div className="login-content">
            {isRegistering ? (
              <>
                <span className="eyebrow">JOIN SWAPNOPURON</span>
                <h2>Create your account.</h2>
                <p className="subtitle">
                  Register as a candidate to begin your recruitment journey.
                </p>

                <form onSubmit={handleRegister}>
                  <label htmlFor="register-name">Full name</label>
                  <input
                    id="register-name"
                    type="text"
                    placeholder="Your full name"
                    minLength={1}
                    maxLength={200}
                    autoComplete="name"
                    value={registration.full_name}
                    onChange={(event) =>
                      setRegistration({
                        ...registration,
                        full_name: event.target.value,
                      })
                    }
                    required
                  />

                  <label htmlFor="register-email">Email address</label>
                  <input
                    id="register-email"
                    type="email"
                    placeholder="you@example.com"
                    autoComplete="email"
                    value={registration.email}
                    onChange={(event) =>
                      setRegistration({
                        ...registration,
                        email: event.target.value,
                      })
                    }
                    required
                  />

                  <label htmlFor="register-password">Password</label>
                  <input
                    id="register-password"
                    type="password"
                    placeholder="At least 8 characters"
                    minLength={8}
                    maxLength={128}
                    autoComplete="new-password"
                    value={registration.password}
                    onChange={(event) =>
                      setRegistration({
                        ...registration,
                        password: event.target.value,
                      })
                    }
                    required
                  />

                  {registrationError && (
                    <p
                      className="form-message form-error"
                      role="alert"
                    >
                      {registrationError}
                    </p>
                  )}

                  <button
                    className="sign-in-button"
                    type="submit"
                    disabled={registrationLoading}
                  >
                    {registrationLoading
                      ? "Creating account..."
                      : "Create account"}
                  </button>
                </form>

                <p className="login-note">
                  Already have an account?{" "}
                  <button
                    type="button"
                    className="auth-switch-button"
                    onClick={() => {
                      setIsRegistering(false);
                      setRegistrationError("");
                    }}
                  >
                    Sign in
                  </button>
                </p>
              </>
            ) : (
              <>
                <span className="eyebrow">WELCOME BACK</span>
                <h2>Good to see you.</h2>
                <p className="subtitle">
                  Sign in to manage applications, interviews, and your
                  recruitment journey.
                </p>

                {registrationSuccess && (
                  <p
                    className="form-message form-success"
                    role="status"
                  >
                    {registrationSuccess}
                  </p>
                )}

                <form onSubmit={handleSubmit}>
                  <label htmlFor="email">Email address</label>
                  <input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    autoComplete="email"
                    required
                  />

                  <div className="password-heading">
                    <label htmlFor="password">Password</label>
                  </div>

                  <div className="password-input">
                    <input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Enter your password"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      autoComplete="current-password"
                      required
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? "Hide" : "Show"}
                    </button>
                  </div>

                  {error && (
                    <p
                      className="form-message form-error"
                      role="alert"
                    >
                      {error}
                    </p>
                  )}

                  <button
                    className="sign-in-button"
                    type="submit"
                    disabled={loading}
                  >
                    {loading ? "Signing in..." : "Sign in"}
                    {!loading && <span aria-hidden="true">→</span>}
                  </button>
                </form>

                <p className="login-note">
                  New to Swapnopuron?{" "}
                  <button
                    type="button"
                    className="auth-switch-button"
                    onClick={() => {
                      setIsRegistering(true);
                      setRegistrationError("");
                      setRegistrationSuccess("");
                      setError("");
                      setRegistration({
                        full_name: "",
                        email: email,
                        password: "",
                      });
                    }}
                  >
                    Create an account
                  </button>
                </p>

                <p className="login-note">
                  Secure access for staff, interviewers, and candidates.
                </p>
              </>
            )}
          </div>

          <footer className="login-footer">
            <span>Swapnopuron Welfare Society</span>
            <span>Recruitment Portal</span>
          </footer>
        </section>

        <aside className="visual-panel">
          <div className="visual-overlay">
            <span className="visual-label">
              PEOPLE · PURPOSE · POSSIBILITY
            </span>
            <div className="visual-copy">
              <h2>Every opportunity can change a future.</h2>
              <p>
                Bringing people and purpose together to create meaningful
                opportunities for the communities we serve.
              </p>
            </div>
            <div className="visual-bottom">
              <span>Building brighter futures, together.</span>
              <span>01 / RECRUITMENT</span>
            </div>
          </div>
        </aside>
      </main>
    );
  }

  const roleLabel = roleLabels[user.role] ?? user.role;
  const canManage = user.role === "admin" || user.role === "staff";

  const filteredApplications = allApplications.filter((item) => {
  const query = applicationSearch.trim().toLowerCase();

  const matchesSearch =
    !query ||
    [
      item.candidate_name,
      item.candidate_email,
      item.candidate_phone,
      item.candidate_education,
      item.candidate_skills,
      item.candidate_experience,
      String(item.id),
      String(item.candidate_id),
      String(item.opportunity_id),
      item.status,
    ].some((value) => String(value ?? "").toLowerCase().includes(query));

  const matchesStatus =
    applicationStatusFilter === "all" ||
    item.status === applicationStatusFilter;

  const matchesOpportunity =
    applicationOpportunityFilter === "all" ||
    String(item.opportunity_id) === applicationOpportunityFilter;

  return matchesSearch && matchesStatus && matchesOpportunity;
});




  const openCount = opportunities.filter(
    (item) => item.status === "open",
  ).length;

  return (
    <main className="dashboard-page">
      <header className="dashboard-header">
        <div className="brand">
          <div className="brand-mark">S</div>
          <div>
            <h1>Swapnopuron</h1>
            <p>RECRUITMENT &amp; PEOPLE</p>
          </div>
        </div>

        <div className="header-user">
          <span>{user.full_name}</span>
          <button className="logout-button" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </header>

      <div className="dashboard-layout">
        <nav className="sidebar" aria-label="Main navigation">
          <span className="sidebar-label">WORKSPACE</span>

          <button
            className={`nav-item ${page === "overview" ? "active" : ""}`}
            onClick={() => setPage("overview")}
          >
            <span>⌂</span> Overview
          </button>

          <button
            className={`nav-item ${
              page === "opportunities" ? "active" : ""
            }`}
            onClick={() => setPage("opportunities")}
          >
            <span>▤</span> Opportunities
          </button>

          {user.role === "candidate" && <>
            <button className={`nav-item ${page === "profile" ? "active" : ""}`} onClick={() => setPage("profile")}><span>◉</span> My Profile</button>
            <button className={`nav-item ${page === "my-applications" ? "active" : ""}`} onClick={() => setPage("my-applications")}><span>▧</span> My Applications</button>
          </>}
          {canManage && <button className={`nav-item ${page === "applications" ? "active" : ""}`} onClick={() => setPage("applications")}><span>☷</span> Applications</button>}
          <button className={`nav-item ${page === "interviews" ? "active" : ""}`} onClick={() => setPage("interviews")}><span>◷</span> Interviews</button>
          {user.role === "interviewer" && <button className={`nav-item ${page === "feedback" ? "active" : ""}`} onClick={() => setPage("feedback")}><span>✓</span> Interview Feedback</button>}
          {canManage && <button className={`nav-item ${page === "feedback" ? "active" : ""}`} onClick={() => setPage("feedback")}><span>✓</span> Interview Feedback</button>}

          <div className="sidebar-profile">
            <span className="profile-avatar">
              {user.full_name.trim().charAt(0).toUpperCase()}
            </span>
            <div>
              <strong>{user.full_name}</strong>
              <small>{roleLabel}</small>
            </div>
          </div>
        </nav>

        <section className="dashboard-main">
          {page === "overview" ? (
            <>
              <div className="dashboard-title-row">
                <div>
                  <span className="eyebrow">{roleLabel.toUpperCase()} DASHBOARD</span>
                  <h2>Welcome, {user.full_name}.</h2>
                  <p className="subtitle">
                    A live overview of your recruitment activity at Swapnopuron.
                  </p>
                </div>
                <button className="secondary-action" type="button" onClick={() => setPage("opportunities")}>
                  View opportunities →
                </button>
              </div>

              {dashboardError && (
                <div className="state-card error-state" role="alert">
                  <p>{dashboardError}</p>
                  <button className="secondary-action" type="button" onClick={() => setDashboardRefresh((value) => value + 1)}>Retry dashboard</button>
                </div>
              )}

              {dashboardLoading ? (
                <div className="state-card">Loading live dashboard metrics…</div>
              ) : (
                <>
                  <div className="dashboard-kpi-grid">
                    <article className="dashboard-kpi-card kpi-opportunities">
                      <div className="kpi-icon" aria-hidden="true">▤</div>
                      <span>OPEN OPPORTUNITIES</span>
                      <strong>{dashboardOpportunities.filter((item) => item.status === "open").length}</strong>
                      <small>Currently accepting applications</small>
                    </article>
                    <article className="dashboard-kpi-card kpi-applications">
                      <div className="kpi-icon" aria-hidden="true">▧</div>
                      <span>{user.role === "candidate" ? "YOUR APPLICATIONS" : "TOTAL APPLICATIONS"}</span>
                      <strong>{dashboardApplications.length}</strong>
                      <small>{user.role === "candidate" ? "Applications submitted by you" : "Across all opportunities"}</small>
                    </article>
                    <article className="dashboard-kpi-card kpi-interviews">
                      <div className="kpi-icon" aria-hidden="true">◷</div>
                      <span>{user.role === "candidate" ? "YOUR INTERVIEWS" : "SCHEDULED INTERVIEWS"}</span>
                      <strong>{dashboardInterviews.filter((item) => item.status === "scheduled").length}</strong>
                      <small>{user.role === "candidate" ? "Interviews scheduled for you" : "Awaiting completion"}</small>
                    </article>
                    <article className="dashboard-kpi-card kpi-selected">
                      <div className="kpi-icon" aria-hidden="true">✓</div>
                      <span>{user.role === "candidate" ? "SELECTED" : "SELECTED CANDIDATES"}</span>
                      <strong>{dashboardApplications.filter((item) => item.status === "selected").length}</strong>
                      <small>Applications marked selected</small>
                    </article>
                  </div>

                  <div className="dashboard-content-grid">
                    {canManage ? (
                      <section className="dashboard-panel">
                        <div className="dashboard-panel-heading">
                          <div><span className="card-label">APPLICATION PIPELINE</span><h3>Applications by stage</h3></div>
                          <button className="text-action" type="button" onClick={() => setPage("applications")}>View all</button>
                        </div>
                        <div className="pipeline-list">
                          {APPLICATION_STATUSES.map((status) => {
                            const count = dashboardApplications.filter((item) => item.status === status).length;
                            const total = dashboardApplications.length;
                            const width = total ? Math.round((count / total) * 100) : 0;
                            return <div className="pipeline-row" key={status}>
                              <div className="pipeline-label"><span>{status.charAt(0).toUpperCase() + status.slice(1)}</span><strong>{count}</strong></div>
                              <div className="pipeline-track" aria-label={`${count} applications ${status}`}><span className={`pipeline-fill pipeline-${status}`} style={{ width: `${width}%` }} /></div>
                            </div>;
                          })}
                        </div>
                        {dashboardApplications.length === 0 && <p className="dashboard-empty-note">Application stages will appear here when candidates apply.</p>}
                      </section>
                    ) : (
                      <section className="dashboard-panel">
                        <div className="dashboard-panel-heading">
                          <div><span className="card-label">{user.role === "candidate" ? "YOUR JOURNEY" : "YOUR WORKLOAD"}</span><h3>{user.role === "candidate" ? "Application progress" : "Interview progress"}</h3></div>
                          <button className="text-action" type="button" onClick={() => setPage(user.role === "candidate" ? "my-applications" : "interviews")}>View details</button>
                        </div>
                        {user.role === "candidate" ? (
                          <div className="personal-progress-list">
                            {APPLICATION_STATUSES.filter((status) => dashboardApplications.some((item) => item.status === status)).map((status) => <div className="personal-progress-item" key={status}><span className={`status-dot status-dot-${status}`} /><span>{status.charAt(0).toUpperCase() + status.slice(1)}</span><strong>{dashboardApplications.filter((item) => item.status === status).length}</strong></div>)}
                            {dashboardApplications.length === 0 && <p className="dashboard-empty-note">You haven't applied for an opportunity yet. Explore open opportunities to get started.</p>}
                          </div>
                        ) : (
                          <div className="personal-progress-list">
                            <div className="personal-progress-item"><span className="status-dot status-dot-scheduled" /><span>Scheduled interviews</span><strong>{dashboardInterviews.filter((item) => item.status === "scheduled").length}</strong></div>
                            <div className="personal-progress-item"><span className="status-dot status-dot-completed" /><span>Completed interviews</span><strong>{dashboardInterviews.filter((item) => item.status === "completed").length}</strong></div>
                            <div className="personal-progress-item"><span className="status-dot status-dot-cancelled" /><span>Cancelled interviews</span><strong>{dashboardInterviews.filter((item) => item.status === "cancelled").length}</strong></div>
                          </div>
                        )}
                      </section>
                    )}

                    <section className="dashboard-panel">
                      <div className="dashboard-panel-heading">
                        <div><span className="card-label">INTERVIEW SCHEDULE</span><h3>{canManage ? "Recent interviews" : "Your interviews"}</h3></div>
                        <button className="text-action" type="button" onClick={() => setPage("interviews")}>View all</button>
                      </div>
                      {dashboardInterviews.length === 0 ? <p className="dashboard-empty-note">No interviews to show yet.</p> : (
                        <div className="dashboard-interview-list">
                          {[...dashboardInterviews].sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime()).slice(0, 4).map((item) => (
                            <div className="dashboard-interview-row" key={item.id}>
                              <div className="interview-date-tile"><strong>{new Date(item.scheduled_at).toLocaleDateString(undefined, { day: "2-digit" })}</strong><span>{new Date(item.scheduled_at).toLocaleDateString(undefined, { month: "short" })}</span></div>
                              <div className="dashboard-interview-info"><strong>Application #{item.application_id}</strong><span>{new Date(item.scheduled_at).toLocaleString(undefined, { hour: "numeric", minute: "2-digit" })}</span></div>
                              <span className={`status-badge ${item.status === "scheduled" ? "status-open" : "status-closed"}`}>{item.status}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </section>
                  </div>

                  <section className="dashboard-bottom-banner">
                    <div><span className="card-label">QUICK ACTION</span><h3>{canManage ? "Keep recruitment moving" : user.role === "candidate" ? "Find your next opportunity" : "Stay ready for your interviews"}</h3><p>{canManage ? "Review applications, update candidate stages, and keep interviews on track." : user.role === "candidate" ? "Explore current openings and check the progress of your applications." : "Review your assigned interviews and submit feedback after completing an interview."}</p></div>
                    <button className="primary-action" type="button" onClick={() => setPage(canManage ? "applications" : user.role === "candidate" ? "opportunities" : "interviews")}>{canManage ? "Review applications →" : user.role === "candidate" ? "Explore opportunities →" : "View interviews →"}</button>
                  </section>
                </>
              )}
            </>
          ) : page === "opportunities" ? (
            <>
              <div className="page-heading">
                <div>
                  <span className="eyebrow">RECRUITMENT</span>
                  <h2>Opportunities</h2>
                  <p className="subtitle">
                    Explore roles and track their current status.
                  </p>
                </div>

                <button
                  className="secondary-action"
                  onClick={() => setPage("overview")}
                >
                  ← Overview
                </button>
              </div>

              {canManage && (
                <div className="create-opportunity-panel">
                  <button
                    className="primary-action"
                    onClick={() => {
                      setShowCreateForm((shown) => !shown);
                      setCreateError("");
                      setCreateSuccess("");
                      setCloseError("");
                    }}
                  >
                    {showCreateForm
                      ? "Cancel"
                      : "+ Create opportunity"}
                  </button>

                  {showCreateForm && (
                    <form
                      className="create-opportunity-form"
                      onSubmit={handleCreateOpportunity}
                    >
                      <h3>New opportunity</h3>

                      <label htmlFor="opportunity-title">Title</label>
                      <input
                        id="opportunity-title"
                        minLength={3}
                        maxLength={200}
                        required
                        value={newOpportunity.title}
                        onChange={(event) =>
                          setNewOpportunity({
                            ...newOpportunity,
                            title: event.target.value,
                          })
                        }
                      />

                      <label htmlFor="opportunity-description">
                        Description
                      </label>
                      <textarea
                        id="opportunity-description"
                        minLength={10}
                        required
                        rows={4}
                        value={newOpportunity.description}
                        onChange={(event) =>
                          setNewOpportunity({
                            ...newOpportunity,
                            description: event.target.value,
                          })
                        }
                      />

                      <label htmlFor="opportunity-type">
                        Opportunity type
                      </label>
                      <select
                        id="opportunity-type"
                        required
                        value={newOpportunity.opportunity_type}
                        onChange={(event) =>
                          setNewOpportunity({
                            ...newOpportunity,
                            opportunity_type: event.target.value,
                          })
                        }
                      >
                        <option value="Volunteer">Volunteer</option>
                        <option value="Fellowship">Fellowship</option>
                        <option value="Full-time">Full-time</option>
                        <option value="Internship">Internship</option>
                        <option value="Contract">Contract</option>
                      </select>

                      <label htmlFor="opportunity-location">
                        Location
                      </label>
                      <input
                        id="opportunity-location"
                        value={newOpportunity.location}
                        onChange={(event) =>
                          setNewOpportunity({
                            ...newOpportunity,
                            location: event.target.value,
                          })
                        }
                      />

                      {createError && (
                        <p
                          className="form-message form-error"
                          role="alert"
                        >
                          {createError}
                        </p>
                      )}

                      <button
                        className="primary-action"
                        type="submit"
                        disabled={createLoading}
                      >
                        {createLoading
                          ? "Creating..."
                          : "Create opportunity"}
                      </button>
                    </form>
                  )}

                  {createSuccess && (
                    <p
                      className="form-message form-success"
                      role="status"
                    >
                      {createSuccess}
                    </p>
                  )}
                </div>
              )}

              {closeError && (
                <p className="form-message form-error" role="alert">
                  {closeError}
                </p>
              )}

              {!opportunitiesLoading && !opportunitiesError && (
                <div className="opportunity-summary">
                  <div>
                    <span>ALL OPPORTUNITIES</span>
                    <strong>{opportunities.length}</strong>
                  </div>
                  <div>
                    <span>OPEN</span>
                    <strong>{openCount}</strong>
                  </div>
                  <div>
                    <span>CLOSED</span>
                    <strong>{opportunities.length - openCount}</strong>
                  </div>
                </div>
              )}

              {opportunitiesLoading && (
                <div className="state-card">
                  Loading opportunities…
                </div>
              )}

              {opportunitiesError && (
                <div className="state-card error-state" role="alert">
                  <p>{opportunitiesError}</p>
                  <button
                    className="secondary-action"
                    onClick={() => setPage("overview")}
                  >
                    Back to overview
                  </button>
                </div>
              )}

              {!opportunitiesLoading &&
                !opportunitiesError &&
                opportunities.length === 0 && (
                  <div className="state-card">
                    <h3>No opportunities yet</h3>
                    <p>
                      New recruitment opportunities will appear here.
                    </p>
                  </div>
                )}

              {!opportunitiesLoading &&
                !opportunitiesError &&
                opportunities.length > 0 && (
                  <div className="opportunity-list">
                    {opportunities.map((opportunity) => (
                      <article
                        className="opportunity-card"
                        key={opportunity.id}
                      >
                        <div className="opportunity-card-top">
                          <span className="opportunity-type">
                            {opportunity.opportunity_type}
                          </span>
                          <span
                            className={`status-badge ${
                              opportunity.status === "open"
                                ? "status-open"
                                : "status-closed"
                            }`}
                          >
                            {opportunity.status}
                          </span>
                        </div>

                        <h3>{opportunity.title}</h3>
                        <p className="opportunity-description">
                          {opportunity.description}
                        </p>

                        <div className="opportunity-card-footer">
                          <span>
                            ⌖{" "}
                            {opportunity.location ||
                              "Location not specified"}
                          </span>
                          <span>Ref. #{opportunity.id}</span>
                        </div>

                        {canManage && opportunity.status === "open" && (
                          <div className="opportunity-actions">
                            <button
                              type="button"
                              className="close-opportunity-button"
                              disabled={closingOpportunityId !== null}
                              onClick={() =>
                                handleCloseOpportunity(opportunity)
                              }
                            >
                              {closingOpportunityId === opportunity.id
                                ? "Closing..."
                                : "Close opportunity"}
                            </button>
                          </div>
                        )}
                        {user.role === "candidate" && opportunity.status === "open" && (
                          <div className="opportunity-actions">
                            <button type="button" className="primary-action" disabled={applyingOpportunityId !== null || myApplications.some((item) => item.opportunity_id === opportunity.id)} onClick={() => handleApply(opportunity)}>
                              {applyingOpportunityId === opportunity.id ? "Applying..." : myApplications.some((item) => item.opportunity_id === opportunity.id) ? "Already applied" : "Apply now"}
                            </button>
                          </div>
                        )}
                      </article>
                    ))}
                  </div>
                )}

              {canManage && (
                <p className="dashboard-footnote">
                  Manage recruitment opportunities and their current
                  status here.
                </p>
              )}
            </>
          ) : null}

          {page === "profile" && user.role === "candidate" && (
            <section className="feature-page">
              <span className="eyebrow">CANDIDATE</span><h2>My Profile</h2>
              <p className="subtitle">Keep your details up to date for recruitment.</p>
              {profileLoading ? <div className="state-card">Loading profile…</div> : <form className="create-opportunity-form" onSubmit={handleSaveProfile}>
                <label htmlFor="profile-phone">Phone</label><input id="profile-phone" value={profile.phone ?? ""} onChange={(e) => setProfile({ ...profile, phone: e.target.value })} />
                <label htmlFor="profile-education">Education</label><input id="profile-education" value={profile.education ?? ""} onChange={(e) => setProfile({ ...profile, education: e.target.value })} />
                <label htmlFor="profile-skills">Skills</label><textarea id="profile-skills" rows={3} value={profile.skills ?? ""} onChange={(e) => setProfile({ ...profile, skills: e.target.value })} />
                <label htmlFor="profile-experience">Experience</label><textarea id="profile-experience" rows={3} value={profile.experience ?? ""} onChange={(e) => setProfile({ ...profile, experience: e.target.value })} />
                <label htmlFor="profile-resume">Resume path or URL</label><input id="profile-resume" value={profile.resume_path ?? ""} onChange={(e) => setProfile({ ...profile, resume_path: e.target.value })} />
                {profileError && <p className="form-message form-error" role="alert">{profileError}</p>}{profileMessage && <p className="form-message form-success" role="status">{profileMessage}</p>}
                <button className="primary-action" type="submit" disabled={profileSaving}>{profileSaving ? "Saving…" : "Save profile"}</button>
              </form>}
            </section>
          )}

          {page === "my-applications" && user.role === "candidate" && (
            <section className="feature-page"><span className="eyebrow">CANDIDATE</span><h2>My Applications</h2><p className="subtitle">Review the opportunities you have applied for.</p>
              {applicationMessage && <p className="form-message form-success" role="status">{applicationMessage}</p>}
              {applicationsLoading ? <div className="state-card">Loading applications…</div> : applicationsError ? <div className="state-card error-state" role="alert">{applicationsError}</div> : myApplications.length === 0 ? <div className="state-card"><h3>No applications yet</h3><p>Visit Opportunities to apply for an open role.</p></div> : <div className="opportunity-list">{myApplications.map((item) => <article className="opportunity-card" key={item.id}><div className="opportunity-card-top"><span>Application #{item.id}</span><span className="status-badge status-open">{item.status}</span></div><h3>Opportunity #{item.opportunity_id}</h3><p>Submitted: {new Date(item.applied_at).toLocaleString()}</p></article>)}</div>}
            </section>
          )}


{page === "applications" && canManage && (
  <section className="feature-page">
    <span className="eyebrow">RECRUITMENT</span>
    <h2>Applications</h2>
    <p className="subtitle">
      Review candidate profiles, search applications, and update recruitment status.
    </p>

    {applicationMessage && (
      <p className="form-message form-success" role="status">
        {applicationMessage}
      </p>
    )}

    {applicationsError && (
      <p className="form-message form-error" role="alert">
        {applicationsError}
      </p>
    )}

    <div className="application-filters">
      <div>
        <label htmlFor="application-search">Search candidates</label>
        <input
          id="application-search"
          type="search"
          placeholder="Name, email, phone, skills, or ID..."
          value={applicationSearch}
          onChange={(event) => setApplicationSearch(event.target.value)}
        />
      </div>

      <div>
        <label htmlFor="application-status-filter">Filter by status</label>
        <select
          id="application-status-filter"
          value={applicationStatusFilter}
          onChange={(event) => setApplicationStatusFilter(event.target.value)}
        >
          <option value="all">All statuses</option>
          {APPLICATION_STATUSES.map((status) => (
            <option key={status} value={status}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="application-opportunity-filter">
          Filter by opportunity
        </label>
        <select
          id="application-opportunity-filter"
          value={applicationOpportunityFilter}
          onChange={(event) =>
            setApplicationOpportunityFilter(event.target.value)
          }
        >
          <option value="all">All opportunities</option>
          {[...new Set(allApplications.map((item) => item.opportunity_id))]
            .sort((a, b) => a - b)
            .map((opportunityId) => (
              <option key={opportunityId} value={String(opportunityId)}>
                Opportunity #{opportunityId}
              </option>
            ))}
        </select>
      </div>

      <button
        type="button"
        className="secondary-action"
        onClick={() => {
          setApplicationSearch("");
          setApplicationStatusFilter("all");
          setApplicationOpportunityFilter("all");
        }}
      >
        Clear filters
      </button>
    </div>

    <p className="application-results-count">
      Showing {filteredApplications.length} of {allApplications.length} applications
    </p>

    {applicationsLoading ? (
      <div className="state-card">Loading applications…</div>
    ) : allApplications.length === 0 ? (
      <div className="state-card">
        <h3>No applications yet</h3>
        <p>Candidate submissions will appear here.</p>
      </div>
    ) : filteredApplications.length === 0 ? (
      <div className="state-card">
        <h3>No matching applications</h3>
        <p>Try changing your search or clearing the filters.</p>
      </div>
    ) : (
      <div className="opportunity-list">
        {filteredApplications.map((item) => (
          <article className="opportunity-card" key={item.id}>
            <div className="opportunity-card-top">
              <span>Application #{item.id}</span>
              <span className="status-badge status-open">
                {item.status}
              </span>
            </div>

            <h3>{item.candidate_name || `Candidate #${item.candidate_id}`}</h3>

            <p>
              <strong>Email:</strong>{" "}
              {item.candidate_email || "Not provided"}
            </p>

            <p>
              <strong>Phone:</strong>{" "}
              {item.candidate_phone || "Not provided"}
            </p>

            <p>
              <strong>Education:</strong>{" "}
              {item.candidate_education || "Not provided"}
            </p>

            <p>
              <strong>Skills:</strong>{" "}
              {item.candidate_skills || "Not provided"}
            </p>

            <p>
              <strong>Experience:</strong>{" "}
              {item.candidate_experience || "Not provided"}
            </p>

            <p>
              <strong>Candidate ID:</strong> {item.candidate_id}
            </p>

            <p>
              <strong>Opportunity:</strong> #{item.opportunity_id}
            </p>

            <p>
              <strong>Applied:</strong>{" "}
              {new Date(item.applied_at).toLocaleString()}
            </p>

            <label htmlFor={`application-status-${item.id}`}>
              Application status
            </label>

            <select
              id={`application-status-${item.id}`}
              value={item.status}
              disabled={applicationUpdatingId === item.id}
              onChange={(event) =>
                handleApplicationStatus(item.id, event.target.value)
              }
            >
              {APPLICATION_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </option>
              ))}
            </select>

            {applicationUpdatingId === item.id && (
              <p>Updating application status…</p>
            )}

            {item.status === "interview" && (
              <button
                type="button"
                className="primary-action"
                onClick={() => {
                  setSchedulingApplicationId(item.id);

                  setNewInterview({
                    application_id: String(item.id),
                    interviewer_id: "",
                    scheduled_at: "",
                    meeting_link: "",
                  });

                  setInterviewsError("");
                  setInterviewMessage("");
                  setShowScheduleForm(true);
                  void loadInterviewers();
                  setPage("interviews");
                }}
              >
                Schedule Interview
              </button>
            )}

          </article>
        ))}
      </div>
    )}
  </section>
)}


          {page === "feedback" && (
            <section className="feature-page">
              <span className="eyebrow">{user.role.toUpperCase()}</span>
              <h2>Interview Feedback</h2>
              <p className="subtitle">Submit evaluation for completed interviews, or review feedback already recorded.</p>
              {feedbackMessage && <p className="form-message form-success" role="status">{feedbackMessage}</p>}
              {feedbackError && <p className="form-message form-error" role="alert">{feedbackError}</p>}
              {feedbackLoading ? <div className="state-card">Loading completed interviews…</div>
                : interviews.length === 0 && Object.keys(feedbackByInterview).length === 0
                  ? <div className="state-card"><h3>No completed interviews found</h3><p>Interviews must be marked completed before feedback can be submitted.</p><button className="secondary-action" type="button" onClick={() => setPage("interviews")}>Open Interviews</button></div>
                  : <div className="opportunity-list">{interviews.filter((item) => item.status === "completed").map((item) => {
                    const existing = feedbackByInterview[item.id];
                    const form = feedbackFormByInterview[item.id] || {
                      technical_score: "3",
                      communication_score: "3",
                      problem_solving_score: "3",
                      comments: "",
                      recommendation: "consider",
                    };
                    return <article className="opportunity-card" key={item.id}>
                      <div className="opportunity-card-top"><span>Interview #{item.id}</span><span className="status-badge status-open">{item.status}</span></div>
                      <h3>Application #{item.application_id}</h3>
                      {existing ? <>
                        <p><strong>Technical:</strong> {existing.technical_score}/5 · <strong>Communication:</strong> {existing.communication_score}/5 · <strong>Problem solving:</strong> {existing.problem_solving_score}/5</p>
                        <p><strong>Recommendation:</strong> {existing.recommendation}</p>
                        <p>{existing.comments}</p>
                      </> : user.role === "interviewer" ? <form className="create-opportunity-form" onSubmit={(event) => handleSubmitFeedback(event, item.id)}>
                        <p className="subtitle">Rate each area from 1 to 5.</p>
                        <label htmlFor={`technical-${item.id}`}>Technical score (1–5)</label>
                        <select id={`technical-${item.id}`} required value={form.technical_score} onChange={(e) => setFeedbackFormByInterview((current) => ({ ...current, [item.id]: { ...form, technical_score: e.target.value } }))}>{[1,2,3,4,5].map((score) => <option key={score} value={score}>{score}</option>)}</select>
                        <label htmlFor={`communication-${item.id}`}>Communication score (1–5)</label>
                        <select id={`communication-${item.id}`} required value={form.communication_score} onChange={(e) => setFeedbackFormByInterview((current) => ({ ...current, [item.id]: { ...form, communication_score: e.target.value } }))}>{[1,2,3,4,5].map((score) => <option key={score} value={score}>{score}</option>)}</select>
                        <label htmlFor={`problem-solving-${item.id}`}>Problem-solving score (1–5)</label>
                        <select id={`problem-solving-${item.id}`} required value={form.problem_solving_score} onChange={(e) => setFeedbackFormByInterview((current) => ({ ...current, [item.id]: { ...form, problem_solving_score: e.target.value } }))}>{[1,2,3,4,5].map((score) => <option key={score} value={score}>{score}</option>)}</select>
                        <label htmlFor={`recommendation-${item.id}`}>Recommendation</label>
                        <select id={`recommendation-${item.id}`} required value={form.recommendation} onChange={(e) => setFeedbackFormByInterview((current) => ({ ...current, [item.id]: { ...form, recommendation: e.target.value } }))}>
                          <option value="selected">Selected</option><option value="consider">Consider</option><option value="rejected">Rejected</option>
                        </select>
                        <label htmlFor={`comments-${item.id}`}>Comments</label>
                        <textarea id={`comments-${item.id}`} required rows={4} value={form.comments} onChange={(e) => setFeedbackFormByInterview((current) => ({ ...current, [item.id]: { ...form, comments: e.target.value } }))} />
                        <button className="primary-action" type="submit" disabled={feedbackSubmittingId === item.id}>{feedbackSubmittingId === item.id ? "Submitting…" : "Submit feedback"}</button>
                      </form> : <p>Feedback has not been submitted for this interview yet.</p>}
                    </article>;
                  })}</div>}
            </section>
          )}

          {page === "interviews" && (
            <section className="feature-page">
              <span className="eyebrow">{canManage ? "RECRUITMENT" : user.role.toUpperCase()}</span>
              <h2>Interviews</h2>
              <p className="subtitle">
                {canManage ? "Schedule interviews and manage their status." : "View your scheduled interviews and meeting details."}
              </p>
              {interviewMessage && <p className="form-message form-success" role="status">{interviewMessage}</p>}
              {interviewsError && <p className="form-message form-error" role="alert">{interviewsError}</p>}

              {canManage && (
                <div className="create-opportunity-panel">
                  <button className="primary-action" type="button" onClick={() => { setShowScheduleForm((shown) => !shown); setInterviewsError(""); setInterviewMessage(""); }}>
                    {showScheduleForm ? "Cancel" : "+ Schedule interview"}
                  </button>
                  {showScheduleForm && (
                    <form className="create-opportunity-form" onSubmit={handleScheduleInterview}>
                      <h3>Schedule an interview</h3>
<p className="subtitle">
  Schedule an interview for an application in interview status.
</p>

<label htmlFor="interview-application-id">Application ID</label>
<input
  id="interview-application-id"
  type="number"
  min="1"
  required
  readOnly={schedulingApplicationId !== null}
  value={newInterview.application_id}
  onChange={(e) =>
    setNewInterview({
      ...newInterview,
      application_id: e.target.value,
    })
  }
/>
                      <label htmlFor="interview-interviewer-id">Interviewer</label>
<select
  id="interview-interviewer-id"
  required
  value={newInterview.interviewer_id}
  onFocus={() => {
    if (interviewers.length === 0) {
      void loadInterviewers();
    }
  }}
  onChange={(e) =>
    setNewInterview({
      ...newInterview,
      interviewer_id: e.target.value,
    })
  }
>
  <option value="">Select an interviewer</option>
  {interviewers.map((interviewer) => (
    <option key={interviewer.id} value={String(interviewer.id)}>
      {interviewer.full_name} ({interviewer.email})
    </option>
  ))}
</select>
                      <label htmlFor="interview-scheduled-at">Date and time (India time)</label>
                      <input id="interview-scheduled-at" type="datetime-local" required value={newInterview.scheduled_at} onChange={(e) => setNewInterview({ ...newInterview, scheduled_at: e.target.value })} />
                      <label htmlFor="interview-meeting-link">Meeting link (optional)</label>
                      <input id="interview-meeting-link" type="url" placeholder="https://…" value={newInterview.meeting_link} onChange={(e) => setNewInterview({ ...newInterview, meeting_link: e.target.value })} />
                      <button className="primary-action" type="submit" disabled={schedulingInterview}>{schedulingInterview ? "Scheduling…" : "Schedule interview"}</button>
                    </form>
                  )}
                </div>
              )}

              {interviewsLoading ? <div className="state-card">Loading interviews…</div>
                : interviews.length === 0 ? <div className="state-card"><h3>No interviews yet</h3><p>{canManage ? "Schedule an interview after an application reaches the interview stage." : "Any interviews assigned to you will appear here."}</p></div>
                : <div className="opportunity-list">{interviews.map((item) => (
                  <article className="opportunity-card" key={item.id}>
                    <div className="opportunity-card-top">
                      <span>Interview #{item.id}</span>
                      <span className={`status-badge ${item.status === "scheduled" ? "status-open" : "status-closed"}`}>{item.status}</span>
                    </div>
                    <h3>Application #{item.application_id}</h3>
                    <p><strong>Scheduled:</strong> {new Date(item.scheduled_at).toLocaleString()}</p>
                    <p><strong>Interviewer user ID:</strong> {item.interviewer_id}</p>
                    {item.meeting_link && <p><strong>Meeting link:</strong> <a href={item.meeting_link} target="_blank" rel="noreferrer">{item.meeting_link}</a></p>}

{canManage && item.status === "scheduled" && (
  <div className="opportunity-actions">
    <button
      type="button"
      className="secondary-action"
      disabled={interviewUpdatingId === item.id || rescheduleLoading}
      onClick={() => {
        setRescheduleError("");
        setRescheduleDateTime(
          new Date(item.scheduled_at)
            .toLocaleString("sv-SE", {
              timeZone: "Asia/Kolkata",
              hour12: false,
            })
            .replace(" ", "T")
            .slice(0, 16),
        );
        setRescheduleInterviewerId(String(item.interviewer_id));
        setRescheduleMeetingLink(item.meeting_link ?? "");
        setReschedulingInterviewId(item.id);
        void loadInterviewers();
      }}
    >
      Reschedule
    </button>

    <button
      type="button"
      className="secondary-action"
      disabled={interviewUpdatingId === item.id || rescheduleLoading}
      onClick={() => handleInterviewStatus(item.id, "completed")}
    >
      {interviewUpdatingId === item.id ? "Updating…" : "Mark completed"}
    </button>

    <button
      type="button"
      className="close-opportunity-button"
      disabled={interviewUpdatingId === item.id || rescheduleLoading}
      onClick={() => handleInterviewStatus(item.id, "cancelled")}
    >
      Cancel interview
    </button>
  </div>
)}

{reschedulingInterviewId === item.id && (
  <form
    className="create-opportunity-form"
    onSubmit={(event) => handleRescheduleInterview(event, item.id)}
  >
    <h3>Reschedule interview #{item.id}</h3>

    {rescheduleError && (
      <p className="form-error" role="alert">{rescheduleError}</p>
    )}

    <label htmlFor={`reschedule-interviewer-${item.id}`}>Interviewer</label>
    <select
      id={`reschedule-interviewer-${item.id}`}
      required
      value={rescheduleInterviewerId}
      onFocus={() => {
        if (interviewers.length === 0) void loadInterviewers();
      }}
      onChange={(event) => setRescheduleInterviewerId(event.target.value)}
    >
      <option value="">Select an interviewer</option>
      {interviewers.map((interviewer) => (
        <option key={interviewer.id} value={String(interviewer.id)}>
          {interviewer.full_name} ({interviewer.email})
        </option>
      ))}
    </select>

    <label htmlFor={`reschedule-datetime-${item.id}`}>
      New date and time (India time)
    </label>
    <input
      id={`reschedule-datetime-${item.id}`}
      type="datetime-local"
      required
      value={rescheduleDateTime}
      onChange={(event) => setRescheduleDateTime(event.target.value)}
    />

    <label htmlFor={`reschedule-link-${item.id}`}>Meeting link (optional)</label>
    <input
      id={`reschedule-link-${item.id}`}
      type="url"
      placeholder="https://…"
      value={rescheduleMeetingLink}
      onChange={(event) => setRescheduleMeetingLink(event.target.value)}
    />

    <button type="submit" className="primary-action" disabled={rescheduleLoading}>
      {rescheduleLoading ? "Rescheduling…" : "Save changes"}
    </button>

    <button
      type="button"
      className="secondary-action"
      disabled={rescheduleLoading}
      onClick={() => {
        setReschedulingInterviewId(null);
        setRescheduleError("");
      }}
    >
      Keep existing schedule
    </button>
  </form>
)}
                  </article>
                ))}
                            </div>}
            </section>
          )}
        </section>
      </div>
    </main>
  );
}

export default App;
