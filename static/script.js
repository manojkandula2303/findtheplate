function uploadFile() {
  let fileInput = document.getElementById("fileInput").files[0];
  let formData = new FormData();
  formData.append("file", fileInput);

  fetch("/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        alert(data.error);
      } else {
        document.querySelector("#result span").textContent = data.plate_number;
        document.getElementById("uploadedImage").src = data.image_path;
      }
    })
    .catch((err) => console.error(err));
}
