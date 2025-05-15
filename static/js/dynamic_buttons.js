
// This script handles changing the "generate playlist" button text while the playlist is being generated
// Also sets the text of the new playlist name button and playlist description to "Please wait..." while the playlist is being generated

// get generate playlist button
const form = document.getElementById("generate-form");
const button = document.getElementById("generate-button");

// get new playlist name button/desc
const playlistDesc = document.getElementById("playlist-desc");
const playlistNameButton = document.getElementById("playlist-name-button");

form.addEventListener("submit", () => {
    // disable both buttons and change text
    button.disabled = true;
    button.textContent = "Generating... Please wait!";

    playlistNameButton.disabled = true;
    playlistDesc.textContent = "Generating your new playlist right now! The button below will link to your new playlist once it is ready.";
    playlistNameButton.textContent = "Please wait...";

    // all of this gets reset on page reload, page is auto reloaded after playlist is generated
});