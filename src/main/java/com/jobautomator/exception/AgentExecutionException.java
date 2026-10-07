package com.jobautomator.exception;

/**
 * Thrown when an agent execution or AI reasoning pipeline fails.
 */
public class AgentExecutionException extends JobAutomatorException {
    private final String agentName;

    public AgentExecutionException(String agentName, String message) {
        super(String.format("[%s] %s", agentName, message));
        this.agentName = agentName;
    }

    public AgentExecutionException(String agentName, String message, Throwable cause) {
        super(String.format("[%s] %s", agentName, message), cause);
        this.agentName = agentName;
    }

    public String getAgentName() {
        return agentName;
    }
}
