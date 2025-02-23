(function ($) {
  'use strict';

  // ----------------------------
  // AOS
  // ----------------------------
  AOS.init({
    once: true
  });

  
  $(window).on('scroll', function () {
    //.Scroll to top show/hide
    var scrollToTop = $('.scroll-top-to'),
      scroll = $(window).scrollTop();
    if (scroll >= 200) {
      scrollToTop.fadeIn(200);
    } else {
      scrollToTop.fadeOut(100);
    }
  });

  // scroll-to-top
  $('.scroll-top-to').on('click', function () {
    $('body,html').animate({
      scrollTop: 0
    }, 500);
    return false;
  });

  $(document).ready(function() {

    // navbarDropdown
    if ($(window).width() < 992) {
      $('.main-nav .dropdown-toggle').on('click', function () {
        $(this).siblings('.dropdown-menu').animate({
          height: 'toggle'
        }, 300);
      });
    }

    // -----------------------------
    //  Testimonial Slider
    // -----------------------------
    $('.testimonial-slider').slick({
      slidesToShow: 2,
      infinite: true,
      arrows: false,
      autoplay: true,
      autoplaySpeed: 2000,
      dots: true,
      responsive: [
        {
          breakpoint: 991,
          settings: {
            slidesToShow: 1,
            slidesToScroll: 1
          }
        }
      ]
    });

    // -----------------------------
    //  Video Replace
    // -----------------------------
    $('.video-box i').click(function () {
      var video = '<iframe class="border-0" allowfullscreen src="' + $(this).attr('data-video') + '"></iframe>';
      $(this).replaceWith(video);
    });

    // -----------------------------
    //  Count Down JS
    // -----------------------------
    var syoTimer = $('#simple-timer');
    if (syoTimer) {
      $('#simple-timer').syotimer({
        year: 2023,
        month: 9,
        day: 1,
        hour: 0,
        minute: 0
      });
    }

    // -----------------------------
    //  Story Slider
    // -----------------------------
    $('.about-slider').slick({
      slidesToShow: 1,
      infinite: true,
      arrows: false,
      autoplay: true,
      autoplaySpeed: 2000,
      dots: true
    });

    // -----------------------------
    //  Quote Slider
    // -----------------------------
    $('.quote-slider').slick({
      slidesToShow: 1,
      infinite: true,
      arrows: false,
      autoplay: true,
      autoplaySpeed: 2000,
      dots: true
    });

    // -----------------------------
    //  Client Slider
    // -----------------------------
    $('.client-slider').slick({
      slidesToShow: 4,
      infinite: true,
      arrows: false,
      autoplaySpeed: 2000,
      dots: true,
      responsive: [
        {
          breakpoint: 0,
          settings: {
            slidesToShow: 1,
            slidesToScroll: 1
          }
        },
        {
          breakpoint: 575,
          settings: {
            slidesToShow: 2,
            slidesToScroll: 1
          }
        },
        {
          breakpoint: 767,
          settings: {
            slidesToShow: 2,
            slidesToScroll: 2
          }
        },
        {
          breakpoint: 991,
          settings: {
            slidesToShow: 3,
            slidesToScroll: 2
          }
        }
      ]
    });

    // -----------------------------
    function logout() {
            const token = localStorage.getItem("token");

            fetch("http://34.121.13.79/user/logout/", {
                method: "POST",
                headers: {
                    "Authorization": `Token ${token}`
                }
            }).then(() => {
                localStorage.removeItem("token");
                window.location.href = "index.html";
            }).catch(() => {
                alert("Logout failed. Please try again.");
            });
    }
    //  Login API Integration
    // -----------------------------
    $("#login-form").on("submit", async function (event) {
        event.preventDefault();  // Prevent page reload on form submission

        const email = $("#email").val();
        const password = $("#password").val();
        const errorMessage = $("#error-message");

        try {
            const response = await fetch("http://34.121.13.79/user/login/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                // Store the token in localStorage
                localStorage.setItem("token", data.token);
                const userConfigResponse = await fetch("http://34.121.13.79/user/current-user-config/", {
                    method: "GET",
                    headers: {
                        "Authorization": `Token ${data.token}`,
                        "Content-Type": "application/json"
                    }
                });
                const userConfigData = await userConfigResponse.json();
                if (userConfigResponse.ok) {
                    const userType = userConfigData.type_of_user;
                    localStorage.setItem("organization_id", userConfigData.organization_id);
                    localStorage.setItem("org_name", userConfigData.org_name);
                    localStorage.setItem("state", userConfigData.state);
                    localStorage.setItem("address", userConfigData.address);
                    localStorage.setItem("pincode", userConfigData.pincode);
                    localStorage.setItem("country", userConfigData.country);

                    // Redirect based on user type
                    if (userType === "org-admin") {
                        window.location.href = "org_admin_dashboard.html";
                    } else if (userType === "teacher") {
                        window.location.href = "teacher_dashboard.html";
                    } else if (userType === "student") {
                        window.location.href = "student_dashboard.html";
                    } else {
                        alert("User type not recognized.");
                        window.location.href = "index.html";  // Default fallback
                    }
                } else {
                    alert("Failed to fetch user configuration.");
                    window.location.href = "index.html";  // Redirect to default if error
                }
            } else {
                errorMessage.text(data.detail || "Invalid credentials.");
                errorMessage.show();
            }
        } catch (error) {
            console.error("Error:", error);
            errorMessage.text("An error occurred. Please try again.");
            errorMessage.show();
        }
    });

  }); // <-- End of $(document).ready()

})(jQuery);
