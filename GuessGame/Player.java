package GuessGame;

public class Player {
	private String name;
	private String team;
	private String position;
	private String conference;

	// default constructor
	public Player(String name, String team, String position, String conference) {
		this.name = name;
		this.team = team;
		this.position = position;
		this.conference = conference;
	}

	// getter methods (accessors) to get the information about the player
	public String getName() {
		return name;
	}

	public String getTeam() {
		return team;
	}

	public String getPosition() {
		return position;
	}

	public String getConference() {
		return conference;
	}

	// return all informaton about a player
	public String toString() {
		return name + " (" + team + ", " + position + ", " + conference + " conference)";
	}
}