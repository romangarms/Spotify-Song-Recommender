
// This script handles changing the "generate playlist" button text while the playlist is being generated

// get generate playlist button
const form = document.getElementById("generate-form");
const button = document.getElementById("generate-button");

// get new playlist name button/desc
const playlistDesc = document.getElementById("playlist-desc");
const playlistNameButton = document.getElementById("playlist-name-button");

form.addEventListener("submit", () => {
    button.disabled = true;
    button.textContent = "Generating... Please wait!";

    playlistNameButton.disabled = true;
    playlistDesc.textContent = "Generating your new playlist right now! The button below will link to your new playlist once it is ready.";
    playlistNameButton.textContent = "Please wait...";
});